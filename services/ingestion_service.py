from retrieval.milvus_store import MilvusStore
from ingestion.pipeline import IngestionPipeline


class IngestionService:
    """Handles document ingestion."""

    def __init__(self):
        self.pipeline = IngestionPipeline()
        self.vector_store = MilvusStore()

    def ingest(
        self,
        file_path: str,
        original_name: str = None,
        doc_status: str = "approved",
        doc_type: str = "general",
    ):
        """Process and index a document with authority metadata."""
        documents = self.pipeline.process(
            file_path,
            original_name=original_name,
            doc_status=doc_status,
            doc_type=doc_type,
        )
        self.vector_store.add_documents(documents)
        return {
            "status": "success",
            "file": original_name or file_path,
            "doc_status": doc_status,
            "doc_type": doc_type,
            "documents_indexed": len(documents),
        }
