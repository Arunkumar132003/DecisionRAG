import time
from memory.chat_history import ChatHistory
from llm.answer_generator import AnswerGenerator
from retrieval.milvus_store import MilvusStore
from retrieval.query_rewriter import QueryRewriter
from retrieval.retriever import Retriever
from retrieval.domain_filter import detect_domain, rerank_by_domain
from services.audit_service import AuditService
from services.governance_service import GovernanceService
from services.ambiguity_service import AmbiguityService
from services.secret_redactor import is_sensitive_request, redact_context, BLOCKED_RESPONSE
from config import CHAT_HISTORY_LIMIT, CHAT_MODEL
from models.response import ChatResponse, SourceCitation


EXCLUDED_STATUSES = {"evaluation_only", "restricted"}
EXCLUDED_TYPES = {"sensitive_data", "evaluation_dataset"}


class ChatService:
    """Main chat orchestration service."""

    def __init__(self):
        self.chat_history = ChatHistory()
        self.vector_store = MilvusStore()
        self.retriever = Retriever(self.vector_store)
        self.query_rewriter = QueryRewriter()
        self.answer_generator = AnswerGenerator()
        self.audit_service = AuditService()
        self.governance = GovernanceService()
        self.ambiguity = AmbiguityService()

    def _filter_documents(self, documents: list) -> list:
        """Remove evaluation artifacts and restricted docs before sending to LLM."""
        return [
            doc for doc in documents
            if doc.metadata.get("doc_status") not in EXCLUDED_STATUSES
            and doc.metadata.get("doc_type") not in EXCLUDED_TYPES
        ]

    def _build_context(self, documents: list) -> str:
        """Build authority-labeled context sorted by authority score descending."""
        sorted_docs = sorted(
            documents,
            key=lambda d: d.metadata.get("authority_score", 2),
            reverse=True
        )
        contexts = []
        for doc in sorted_docs:
            source = doc.metadata.get("source", "unknown")
            status = doc.metadata.get("doc_status", "unknown")
            score = doc.metadata.get("authority_score", 2)
            contexts.append(
                f"[SOURCE: {source} | STATUS: {status} | AUTHORITY: {score}]\n{doc.page_content}"
            )
        return "\n\n".join(contexts)

    def _build_citations(self, documents: list, cited_sources: list[str]) -> list[SourceCitation]:
        """Build SourceCitation objects for sources the LLM cited."""
        source_meta = {}
        for doc in documents:
            name = doc.metadata.get("source", "unknown")
            if name not in source_meta:
                source_meta[name] = {
                    "doc_status": doc.metadata.get("doc_status", "unknown"),
                    "authority_score": doc.metadata.get("authority_score", 2),
                }
        citations = []
        for src in cited_sources:
            meta = source_meta.get(src, {"doc_status": "unknown", "authority_score": 2})
            citations.append(SourceCitation(
                source=src,
                doc_status=meta["doc_status"],
                authority_score=meta["authority_score"],
            ))
        return citations

    def _calibrate_confidence(
        self,
        llm_score: float,
        conflicts_detected: bool,
        missing_information: list,
        assumptions: list,
        citations: list[SourceCitation],
    ) -> float:
        """
        Compute calibrated confidence score.
        - 60% weight on LLM estimate
        - 40% weight on average authority of cited sources (normalized 0-1)
        - Penalties for conflicts, missing info, and assumptions
        """
        if citations:
            avg_authority = sum(c.authority_score for c in citations) / len(citations) / 100
        else:
            avg_authority = 0.3

        base = llm_score * 0.6 + avg_authority * 0.4

        if conflicts_detected:
            base -= 0.15
        base -= min(len(missing_information) * 0.05, 0.20)
        base -= min(len(assumptions) * 0.03, 0.10)

        return max(0.0, min(1.0, round(base, 2)))

    def _blocked_response(self, session_id: str, question: str, message: str) -> ChatResponse:
        """Return a security refusal without hitting retrieval or LLM."""
        return ChatResponse(
            question=question,
            answer=message,
            confidence_score=1.0,
            source_citations=[],
            risk_level="high",
            requires_human_review=True,
            reason_for_review="Question requests sensitive credentials or secrets",
            assumptions=[],
            missing_information=[],
            recommended_next_action="Contact your system administrator for secure access credentials.",
            conflicts_detected=False,
            conflict_explanation="",
            session_id=session_id,
        )

    def _ambiguous_response(self, session_id: str, question: str, message: str) -> ChatResponse:
        """Return a clarification request without hitting retrieval or LLM."""
        return ChatResponse(
            question=question,
            answer=message,
            confidence_score=0.0,
            source_citations=[],
            risk_level="low",
            requires_human_review=False,
            reason_for_review="",
            assumptions=[],
            missing_information=["Clarification needed from user"],
            recommended_next_action="Please rephrase your question with more specific details.",
            conflicts_detected=False,
            conflict_explanation="",
            session_id=session_id,
        )

    def chat(self, session_id: str, question: str, api_key: str = None) -> ChatResponse:
        """Execute complete RAG pipeline with ambiguity check, authority-aware retrieval, and governance."""

        if is_sensitive_request(question):
            return self._blocked_response(session_id, question, BLOCKED_RESPONSE)

        is_ambiguous, clarification = self.ambiguity.check(question)
        if is_ambiguous:
            return self._ambiguous_response(session_id, question, clarification)

        history = self.chat_history.format_history(session_id, limit=CHAT_HISTORY_LIMIT)
        rewritten_query = self.query_rewriter.rewrite(question=question, history=history)

        t_retrieval_start = time.perf_counter()
        documents = self.retriever.retrieve(rewritten_query)
        retrieval_latency_ms = (time.perf_counter() - t_retrieval_start) * 1000

        domain = detect_domain(question)
        documents = rerank_by_domain(documents, domain)
        documents = self._filter_documents(documents)

        context = redact_context(self._build_context(documents))
        print(f"\nQuestion: {question}")
        print(f"Domain detected: {domain}")
        print("=" * 60)
        print(f"CHUNKS SENT TO LLM ({len(documents)} docs):")
        print("=" * 60)
        print(context)
        print("=" * 60 + "\n")

        t_response_start = time.perf_counter()
        result = self.answer_generator.generate(question=question, history=history, context=context, api_key=api_key)
        response_latency_ms = (time.perf_counter() - t_response_start) * 1000

        source_statuses = [d.metadata.get("doc_status", "unknown") for d in documents]
        gov_flag, gov_reason = self.governance.evaluate(
            question=question,
            answer=result.answer,
            source_statuses=source_statuses,
        )

        requires_human_review = result.requires_human_review or gov_flag
        reason_for_review = " | ".join(filter(None, [result.reason_for_review, gov_reason]))

        citations = self._build_citations(documents, result.cited_sources)
        confidence_score = self._calibrate_confidence(
            llm_score=result.confidence_score,
            conflicts_detected=result.conflicts_detected,
            missing_information=result.missing_information,
            assumptions=result.assumptions,
            citations=citations,
        )

        citations_serializable = [c.model_dump() for c in citations]
        self.chat_history.add_user_message(session_id, question)
        self.chat_history.add_assistant_message(session_id, result.answer)

        self.audit_service.log(
            session_id=session_id,
            question=question,
            answer=result.answer,
            confidence_score=confidence_score,
            risk_level=result.risk_level,
            requires_human_review=requires_human_review,
            reason_for_review=reason_for_review,
            source_citations=citations_serializable,
            conflicts_detected=result.conflicts_detected,
            conflict_explanation=result.conflict_explanation,
            assumptions=result.assumptions,
            missing_information=result.missing_information,
            recommended_next_action=result.recommended_next_action,
            model_used=CHAT_MODEL,
            retrieval_latency_ms=retrieval_latency_ms,
            response_latency_ms=response_latency_ms,
        )

        return ChatResponse(
            question=question,
            answer=result.answer,
            confidence_score=confidence_score,
            source_citations=citations,
            risk_level=result.risk_level,
            requires_human_review=requires_human_review,
            reason_for_review=reason_for_review,
            assumptions=result.assumptions,
            missing_information=result.missing_information,
            recommended_next_action=result.recommended_next_action,
            conflicts_detected=result.conflicts_detected,
            conflict_explanation=result.conflict_explanation,
            session_id=session_id,
        )
