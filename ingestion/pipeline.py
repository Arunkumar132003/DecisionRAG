from langchain_core.documents import Document
from ingestion.chunker import DocumentChunker
from ingestion.metadata import MetadataBuilder
from ingestion.parser import DocumentParser


class IngestionPipeline:
    """End-to-end ingestion pipeline."""

    def __init__(self):
        self.parser = DocumentParser()
        self.chunker = DocumentChunker()
        self.metadata_builder = MetadataBuilder()

    def process(
        self,
        file_path: str,
        original_name: str = None,
        doc_status: str = "approved",
        doc_type: str = "general",
    ):
        """Convert file into LangChain documents with authority metadata."""
        file_name = original_name or self.parser.get_file_name(file_path)
        document = self.parser.parse(file_path)
        chunks = self.chunker.chunk(document)
        documents = []
        for index, chunk in enumerate(chunks):
            metadata = self.metadata_builder.build(
                file_name=file_name,
                chunk_index=index,
                headings=chunk["headings"],
                doc_status=doc_status,
                doc_type=doc_type,
            )
            documents.append(Document(page_content=chunk["content"], metadata=metadata))
        return documents
