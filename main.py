from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from api.chat import router as chat_router
from api.ingest import router as ingest_router
from api.review import router as review_router
from api.batch import router as batch_router

app = FastAPI(title="Enterprise RAG")

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
app.include_router(review_router, prefix="/review", tags=["review"])
app.include_router(batch_router, prefix="/batch", tags=["batch"])

UI_DIR = Path(__file__).parent / "ui"
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")


@app.get("/")
def index():
    """Serve the frontend UI."""
    return FileResponse(UI_DIR / "index.html")
