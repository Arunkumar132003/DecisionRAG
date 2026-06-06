import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form
from typing import Literal
from services.ingestion_service import IngestionService

router = APIRouter()
ingestion_service = IngestionService()

@router.post("/")
async def ingest(
    file: UploadFile = File(...),
    doc_status: Literal["approved", "legacy", "draft", "informal", "approved_reference", "restricted", "evaluation_only"] = Form(default="approved"),
    doc_type: Literal[
        "security_policy", "data_protection_addendum", "ai_policy",
        "product_faq", "pricing_implementation_note", "company_overview",
        "integration_matrix", "release_notes", "historical_rfp_response",
        "customer_support_email", "sensitive_data", "evaluation_dataset", "general"
    ] = Form(default="general"),
):
    """Document ingestion endpoint. Accepts authority metadata alongside the file."""
    content = await file.read()
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        return ingestion_service.ingest(
            tmp.name,
            original_name=file.filename,
            doc_status=doc_status,
            doc_type=doc_type,
        )
