import csv
import io
import json
from typing import Literal
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()
BATCH_LIMIT = 10

class BatchRequest(BaseModel):
    questions: list[str]
    export_format: Literal["json", "csv"] = "json"

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("questions list must not be empty")
        if len(v) > BATCH_LIMIT:
            raise ValueError(f"batch limit is {BATCH_LIMIT} questions")
        return [q.strip() for q in v if q.strip()]


@router.post("/")
def batch(request: BatchRequest):
    """Process a batch of questions and return results as JSON or CSV."""
    results = []
    for question in request.questions:
        response = chat_service.chat(session_id="batch", question=question)
        results.append(response.model_dump())

    if request.export_format == "csv":
        output = io.StringIO()
        if results:
            flat_fields = [
                "question", "answer", "confidence_score", "risk_level",
                "requires_human_review", "reason_for_review",
                "conflicts_detected", "conflict_explanation",
                "recommended_next_action", "session_id",
            ]
            writer = csv.DictWriter(output, fieldnames=flat_fields, extrasaction="ignore")
            writer.writeheader()
            for row in results:
                writer.writerow({k: row.get(k, "") for k in flat_fields})
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=batch_results.csv"},
        )
    return results
