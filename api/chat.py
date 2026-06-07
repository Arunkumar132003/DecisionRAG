import uuid
from typing import Optional
from fastapi import APIRouter, Cookie, Response, HTTPException
from models.request import ChatRequest
from services.chat_service import ChatService
from llm.answer_generator import RateLimitError

router = APIRouter()
chat_service = ChatService()

@router.post("/")
def chat(
    request: ChatRequest,
    response: Response,
    session_id: Optional[str] = Cookie(default=None)
):
    """Chat endpoint. Session is managed automatically via cookie."""
    if not session_id:
        session_id = uuid.uuid4().hex
        response.set_cookie(key="session_id", value=session_id, httponly=True)
    try:
        return chat_service.chat(session_id=session_id, question=request.question, api_key=request.api_key)
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM rate limit reached. Please wait a moment and try again."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))