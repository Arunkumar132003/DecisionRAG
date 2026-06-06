from pathlib import Path
from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.labels import DocItemLabel


class DocumentParser:
    """Parses documents using Docling, with plain-text fallback for .txt files."""

    def __init__(self):
        self.converter = DocumentConverter()

    def parse(self, file_path: str):
        """Convert document into Docling document."""
        path = Path(file_path)
        if path.suffix.lower() == ".txt":
            return self._parse_txt(path)
        return self.converter.convert(file_path).document

    def get_file_name(self, file_path: str) -> str:
        """Return source file name."""
        return Path(file_path).name

    def _parse_txt(self, path: Path):
        """Build a DoclingDocument from a plain-text file by splitting on blank lines."""
        doc = DoclingDocument(name=path.name)
        text = path.read_text(encoding="utf-8", errors="replace")
        for paragraph in text.split("\n\n"):
            paragraph = paragraph.strip()
            if paragraph:
                doc.add_text(label=DocItemLabel.PARAGRAPH, text=paragraph)
        return doc