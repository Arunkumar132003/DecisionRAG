import json
from pathlib import Path

STATUS_SCORE = {
    "approved": 100,
    "approved_reference": 80,
    "legacy": 30,
    "draft": 20,
    "informal": 10,
    "restricted": 0,
    "evaluation_only": 0,
}

TYPE_SCORE = {
    "security_policy": 100,
    "data_protection_addendum": 95,
    "ai_policy": 95,
    "product_faq": 90,
    "pricing_implementation_note": 90,
    "company_overview": 85,
    "integration_matrix": 85,
    "release_notes": 80,
    "historical_rfp_response": 70,
    "customer_support_email": 10,
    "sensitive_data": 0,
    "evaluation_dataset": 0,
    "general": 50,
}


def compute_authority_score(doc_status: str, doc_type: str) -> int:
    status = STATUS_SCORE.get(doc_status, 50)
    doc = TYPE_SCORE.get(doc_type, 50)
    return round(status * 0.7 + doc * 0.3)


class MetadataBuilder:
    """Build metadata for retrieval, citation, and authority ranking."""

    def build(
        self,
        file_name: str,
        chunk_index: int,
        headings: list,
        doc_status: str = "approved",
        doc_type: str = "general",
    ):
        """Create metadata including source authority fields."""
        return {
            "source": Path(file_name).name,
            "chunk_id": chunk_index,
            "headings": json.dumps(headings),
            "doc_status": doc_status,
            "doc_type": doc_type,
            "authority_score": compute_authority_score(doc_status, doc_type),
        }
