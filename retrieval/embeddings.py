from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from config import EMBEDDING_MODEL


class LocalEmbeddings(Embeddings):
    """Local sentence-transformers embedding model."""

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        return self.model.encode(text, normalize_embeddings=True).tolist()
