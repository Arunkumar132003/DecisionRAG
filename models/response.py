from typing import Literal
from pydantic import BaseModel, Field

class SourceCitation(BaseModel):
    source: str
    doc_status: str
    authority_score: int

class ChatResponse(BaseModel):
    question: str
    answer: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    source_citations: list[SourceCitation]
    risk_level: Literal["low", "medium", "high"]
    requires_human_review: bool
    reason_for_review: str
    assumptions: list[str]
    missing_information: list[str]
    recommended_next_action: str
    conflicts_detected: bool
    conflict_explanation: str
    session_id: str