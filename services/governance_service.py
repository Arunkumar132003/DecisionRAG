import re

EXCLUDED_STATUSES = {"evaluation_only", "restricted"}
EXCLUDED_TYPES = {"sensitive_data", "evaluation_dataset"}

COMMITMENT_PATTERNS = [
    r"\bcan\s+(you|northstar)\s+(commit|guarantee|promise|ensure|confirm)\b",
    r"\bwill\s+(you|northstar)\s+(never|always|guarantee)\b",
    r"\b(commit|guarantee|promise)\s+that\b",
    r"\bdo\s+you\s+(guarantee|promise|commit)\b",
    r"\bnever\s+(leave|store|share|expose|transfer)\b",
]

LEGAL_PATTERNS = [
    r"\bsla\b", r"\bguarantee\b", r"\bwarranty\b", r"\bliabilit\w*\b",
    r"\bindemnif\w*\b", r"\bcontract\w*\b", r"\bagreement\b", r"\bcommitment\b",
]

COMPLIANCE_PATTERNS = [
    r"\bsoc\s*[12]\b", r"\biso\s*2700[12]\b", r"\bgdpr\b", r"\bhipaa\b",
    r"\bpci\b", r"\bcertif\w*\b", r"\bcomplian\w*\b", r"\baudit\b",
    r"\bregulat\w*\b", r"\bdata\s+residency\b", r"\bdata\s+protection\b",
]

SECURITY_PATTERNS = [
    r"\bencryption\b", r"\bpenetration\s+test\b", r"\bvulnerabilit\w*\b",
    r"\bsecurity\s+policy\b", r"\baccess\s+control\b", r"\bauthentication\b",
]

SENSITIVE_DATA_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    r"(?:password|secret|api[_\s]?key|token)\s*[:=]\s*\S+",
]

PRICING_PATTERNS = [
    r"\bpric\w*\b", r"\bcost\b", r"\bdiscount\b", r"\$\d+", r"\bfee\b",
    r"\bimplementation\s+cost\b",
]

DATA_HANDLING_PATTERNS = [
    r"\bdata\s+deletion\b", r"\bretention\b", r"\bpersonal\s+data\b",
    r"\btraining\s+data\b", r"\bdata\s+transfer\b", r"\bsubprocessor\b",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


class GovernanceService:
    """Deterministic rules that enforce human review regardless of LLM output."""

    def evaluate(self, question: str, answer: str, source_statuses: list[str]) -> tuple[bool, str]:
        """
        Returns (requires_human_review, reason).
        Overrides LLM decision when deterministic rules trigger.
        """
        combined = f"{question} {answer}"
        reasons = []

        if _matches_any(combined, LEGAL_PATTERNS):
            reasons.append("contains legal or contractual language")

        if _matches_any(combined, COMPLIANCE_PATTERNS):
            reasons.append("involves compliance certifications or regulatory claims")

        if _matches_any(combined, SECURITY_PATTERNS):
            reasons.append("involves security policy or controls")

        if _matches_any(combined, PRICING_PATTERNS):
            reasons.append("involves pricing or cost commitments")

        if _matches_any(combined, DATA_HANDLING_PATTERNS):
            reasons.append("involves data handling, deletion, or retention")

        if _matches_any(answer, SENSITIVE_DATA_PATTERNS):
            reasons.append("answer may expose sensitive or personal data")

        if "informal" in source_statuses or "email" in source_statuses:
            reasons.append("answer derived from informal or unapproved sources")

        if reasons:
            return True, "; ".join(reasons)

        return False, ""

    def is_commitment_question(self, question: str) -> bool:
        return _matches_any(question, COMMITMENT_PATTERNS)

    def is_excluded_document(self, doc_status: str, doc_type: str) -> bool:
        return doc_status in EXCLUDED_STATUSES or doc_type in EXCLUDED_TYPES

    def contains_sensitive_data(self, text: str) -> bool:
        return _matches_any(text, SENSITIVE_DATA_PATTERNS)