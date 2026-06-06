from typing import Literal
from pydantic import BaseModel, Field


class AnswerAnalysis(BaseModel):
    answer: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high"]
    requires_human_review: bool
    reason_for_review: str
    assumptions: list[str]
    missing_information: list[str]
    recommended_next_action: str
    cited_sources: list[str]
    conflicts_detected: bool
    conflict_explanation: str
