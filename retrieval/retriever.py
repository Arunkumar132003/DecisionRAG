from config import TOP_K_RETRIEVAL
from retrieval.milvus_store import MilvusStore
from retrieval.reranker import Reranker

class Retriever:
    """Hybrid retrieval pipeline."""

    def __init__(self, vector_store: MilvusStore):
        self.vector_store = vector_store
        self.reranker = Reranker()

    def retrieve(self, query: str):
        """Retrieve and rerank documents."""

        documents = self.vector_store.search(query=query, k=TOP_K_RETRIEVAL)
        return self.reranker.rerank(query=query, documents=documents)