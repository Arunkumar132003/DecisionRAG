from typing import Optional
from pydantic import BaseModel, field_validator

class ChatRequest(BaseModel):
    question: str
    api_key: Optional[str] = None

    @field_validator("question")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()