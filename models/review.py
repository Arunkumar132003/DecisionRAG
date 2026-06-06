from typing import Literal, Optional
from pydantic import BaseModel


class ReviewAction(BaseModel):
    comment: Optional[str] = None
    final_answer: Optional[str] = None


class ReviewRecord(BaseModel):
    id: str
    session_id: str
    question: str
    answer: str
    confidence_score: float
    risk_level: str
    requires_human_review: bool
    reason_for_review: str
    source_citations: list
    conflicts_detected: bool
    conflict_explanation: str
    assumptions: list[str]
    missing_information: list[str]
    recommended_next_action: str
    model_used: str
    retrieval_latency_ms: float
    response_latency_ms: float
    created_at: str
    review_status: Literal["pending", "approved", "rejected", "edited"]
    reviewer_comment: Optional[str]
    final_answer: Optional[str]
    reviewed_at: Optional[str]
