from langchain_milvus import Milvus
from retrieval.embeddings import LocalEmbeddings
from retrieval.bm25_retriever import BM25Retriever
from config import MILVUS_COLLECTION
from config import MILVUS_URI


class MilvusStore:
    """Dense vector store with a parallel in-memory BM25 index."""

    def __init__(self):
        self.embeddings = LocalEmbeddings()
        self.bm25 = BM25Retriever()

        self.vector_store = Milvus(
            embedding_function=self.embeddings,
            connection_args={"uri": MILVUS_URI},
            collection_name=MILVUS_COLLECTION,
            auto_id=True,
            drop_old=False
        )
        self._rebuild_bm25_index()

    def _rebuild_bm25_index(self):
        """Load all stored documents from Milvus to rebuild the BM25 index on startup."""
        try:
            results = self.vector_store.similarity_search(query="*", k=10000)
            self.bm25.index(results)
        except Exception:
            self.bm25.index([])

    def add_documents(self, documents):
        """Insert documents into Milvus and update BM25 index."""
        self.vector_store.add_documents(documents)
        all_docs = self.bm25._docs + documents
        self.bm25.index(all_docs)

    def search(self, query: str, k: int):
        """Hybrid search: dense + BM25 fused with RRF."""
        dense_results = self.vector_store.similarity_search(query=query, k=k)
        bm25_results = self.bm25.search(query=query, k=k)
        return _rrf_fuse(dense_results, bm25_results, k=k)

    def get_retriever(self, k: int):
        """Return LangChain retriever (dense only — used internally by LangChain chains)."""
        return self.vector_store.as_retriever(search_kwargs={"k": k})

    def delete_collection(self):
        """Drop collection and clear BM25 index."""
        self.vector_store.drop()
        self.bm25.index([])


def _rrf_fuse(dense: list, bm25: list, k: int, rrf_k: int = 60) -> list:
    """Reciprocal Rank Fusion of two ranked lists."""
    scores: dict[str, float] = {}
    doc_map: dict[str, object] = {}

    for rank, doc in enumerate(dense):
        key = doc.page_content
        scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank + 1)
        doc_map[key] = doc

    for rank, doc in enumerate(bm25):
        key = doc.page_content
        scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank + 1)
        doc_map[key] = doc

    ranked = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [doc_map[key] for key in ranked[:k]]
