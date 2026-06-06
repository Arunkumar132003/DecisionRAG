from fastapi import APIRouter, HTTPException
from models.review import ReviewAction
from services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()

@router.get("/pending")
def get_pending_reviews():
    """List all answers awaiting human review."""
    return audit_service.get_pending_reviews()

@router.get("/all")
def get_all_records():
    """List all audit records."""
    return audit_service.get_all()

@router.get("/{record_id}")
def get_record(record_id: str):
    """Get a single audit record by id."""
    record = audit_service.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.post("/{record_id}/approve")
def approve(record_id: str, body: ReviewAction = ReviewAction()):
    """Approve an answer, optionally with an edited version."""
    updated = audit_service.update_review(
        record_id=record_id,
        review_status="approved",
        reviewer_comment=body.comment,
        final_answer=body.final_answer,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"status": "approved", "id": record_id}

@router.post("/{record_id}/reject")
def reject(record_id: str, body: ReviewAction = ReviewAction()):
    """Reject an answer with a mandatory comment explaining why."""
    if not body.comment:
        raise HTTPException(status_code=400, detail="comment is required when rejecting")
    updated = audit_service.update_review(
        record_id=record_id,
        review_status="rejected",
        reviewer_comment=body.comment,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"status": "rejected", "id": record_id}

@router.post("/{record_id}/edit")
def edit(record_id: str, body: ReviewAction):
    """Approve with an edited final answer."""
    if not body.final_answer:
        raise HTTPException(status_code=400, detail="final_answer is required for an edit")
    updated = audit_service.update_review(
        record_id=record_id,
        review_status="edited",
        reviewer_comment=body.comment,
        final_answer=body.final_answer,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"status": "edited", "id": record_id}
