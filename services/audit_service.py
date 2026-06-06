import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from config import AUDIT_PATH


class AuditService:
    """Stores audit records as JSON, supports human review workflow."""

    def _load(self) -> list:
        path = Path(AUDIT_PATH)
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        return json.loads(text)

    def _save(self, records: list):
        Path(AUDIT_PATH).write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def log(
        self,
        session_id: str,
        question: str,
        answer: str,
        confidence_score: float,
        risk_level: str,
        requires_human_review: bool,
        reason_for_review: str,
        source_citations: list,
        conflicts_detected: bool,
        conflict_explanation: str,
        assumptions: list,
        missing_information: list,
        recommended_next_action: str,
        model_used: str,
        retrieval_latency_ms: float,
        response_latency_ms: float,
    ) -> str:
        """Append a new audit record and return its id."""
        record_id = uuid.uuid4().hex
        record = {
            "id": record_id,
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "confidence_score": confidence_score,
            "risk_level": risk_level,
            "requires_human_review": requires_human_review,
            "reason_for_review": reason_for_review,
            "source_citations": source_citations,
            "conflicts_detected": conflicts_detected,
            "conflict_explanation": conflict_explanation,
            "assumptions": assumptions,
            "missing_information": missing_information,
            "recommended_next_action": recommended_next_action,
            "model_used": model_used,
            "retrieval_latency_ms": round(retrieval_latency_ms, 2),
            "response_latency_ms": round(response_latency_ms, 2),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "review_status": "pending",
            "reviewer_comment": None,
            "final_answer": None,
            "reviewed_at": None,
        }
        records = self._load()
        records.append(record)
        self._save(records)
        return record_id

    def get_all(self) -> list:
        return self._load()

    def get_pending_reviews(self) -> list:
        return [r for r in self._load() if r.get("requires_human_review") and r.get("review_status") == "pending"]

    def get_by_id(self, record_id: str) -> dict | None:
        return next((r for r in self._load() if r["id"] == record_id), None)

    def update_review(self, record_id: str, review_status: str, reviewer_comment: str = None, final_answer: str = None) -> bool:
        """Update review status on an existing record. Returns False if not found."""
        records = self._load()
        for record in records:
            if record["id"] == record_id:
                record["review_status"] = review_status
                record["reviewer_comment"] = reviewer_comment
                record["final_answer"] = final_answer
                record["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                self._save(records)
                return True
        return False
