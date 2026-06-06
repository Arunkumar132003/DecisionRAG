from FlagEmbedding import FlagReranker
from config import RERANKER_MODEL
from config import TOP_K_RERANK


class Reranker:
    """BGE cross-encoder reranker."""

    def __init__(self):
        self.model = FlagReranker(RERANKER_MODEL, use_fp16=True)

    def rerank(self, query: str, documents: list):
        """Rerank documents using a cross-encoder in a single batch call."""
        if not documents:
            return []
        pairs = [[query, doc.page_content] for doc in documents]
        scores = self.model.compute_score(pairs, normalize=True)
        if isinstance(scores, float):
            scores = [scores]
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in ranked[:TOP_K_RERANK]]
