from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

MILVUS_URI = os.getenv("MILVUS_URI", str(STORAGE_DIR / "milvus.db"))
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "enterprise_rag")

CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash-lite")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
TOKENIZER_MODEL = os.getenv("TOKENIZER_MODEL", "bert-base-uncased")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")


TOP_K_RETRIEVAL = 10
TOP_K_RERANK = 5

CHAT_HISTORY_LIMIT = 10

AUDIT_PATH = STORAGE_DIR / "audit.json"