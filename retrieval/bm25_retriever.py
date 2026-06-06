import re
from rank_bm25 import BM25Okapi

def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())

class BM25Retriever:
    """In-memory BM25 retriever built from a document corpus."""

    def __init__(self):
        self._docs = []
        self._corpus_tokens = []
        self._bm25 = None

    def index(self, documents: list):
        """Build BM25 index from a list of LangChain documents."""
        self._docs = documents
        self._corpus_tokens = [_tokenize(doc.page_content) for doc in documents]
        self._bm25 = BM25Okapi(self._corpus_tokens) if self._corpus_tokens else None

    def search(self, query: str, k: int) -> list:
        """Return top-k documents by BM25 score."""
        if not self._bm25 or not self._docs:
            return []
        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self._docs[i] for i in top_indices]