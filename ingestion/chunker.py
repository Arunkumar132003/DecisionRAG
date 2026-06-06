from transformers import AutoTokenizer
from docling.chunking import HybridChunker
from config import TOKENIZER_MODEL

class DocumentChunker:

    def __init__(self):
        tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)
        max_tokens = tokenizer.model_max_length if tokenizer.model_max_length < 1_000_000 else 512
        self.chunker = HybridChunker(tokenizer=tokenizer, max_tokens=max_tokens)

    def chunk(self, document):
        """Generate contextualized chunks."""

        chunks = []
        for chunk in self.chunker.chunk(document):
            chunks.append({
                "content": self.chunker.contextualize(chunk),
                "headings": getattr(chunk, "headings", [])
            })
        return chunks