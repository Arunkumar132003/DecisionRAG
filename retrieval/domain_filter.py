DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "security": [
        "security", "encryption", "access control", "penetration", "soc", "iso",
        "vulnerability", "firewall", "credential", "authentication", "certificate",
        "breach", "threat", "intrusion", "audit log",
    ],
    "privacy": [
        "privacy", "gdpr", "data protection", "personal data", "dpa", "residency",
        "deletion", "retention", "subprocessor", "data transfer", "consent",
    ],
    "ai": [
        "ai", "artificial intelligence", "machine learning", "model training",
        "ai policy", "llm", "generative", "ai usage",
    ],
    "pricing": [
        "pricing", "price", "cost", "fee", "discount", "implementation cost",
        "tier", "plan", "subscription", "billing",
    ],
    "integration": [
        "integration", "api", "connector", "webhook", "crm", "erp",
        "salesforce", "plugin", "sdk", "rest",
    ],
    "product": [
        "product", "feature", "capability", "platform", "workflow", "copilot",
        "functionality", "module", "dashboard",
    ],
    "release": [
        "release", "update", "changelog", "version", "roadmap", "preview",
        "upcoming", "planned", "q1", "q2",
    ],
}

DOMAIN_PREFERRED_TYPES: dict[str, list[str]] = {
    "security": ["security_policy", "data_protection_addendum"],
    "privacy": ["data_protection_addendum", "security_policy"],
    "ai": ["ai_policy"],
    "pricing": ["pricing_implementation_note"],
    "integration": ["integration_matrix", "product_faq"],
    "product": ["product_faq", "company_overview"],
    "release": ["release_notes"],
}

DOMAIN_BOOST = 20


def detect_domain(question: str) -> str | None:
    """Return the most likely domain for a question, or None."""
    q = question.lower()
    best_domain = None
    best_count = 0
    for domain, keywords in DOMAIN_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in q)
        if count > best_count:
            best_count = count
            best_domain = domain
    return best_domain if best_count > 0 else None


def rerank_by_domain(documents: list, domain: str | None) -> list:
    """
    Boost authority_score for documents whose doc_type matches the detected domain.
    Returns documents re-sorted by boosted score.
    """
    if not domain:
        return documents

    preferred = DOMAIN_PREFERRED_TYPES.get(domain, [])

    def boosted_score(doc) -> int:
        base = doc.metadata.get("authority_score", 50)
        if doc.metadata.get("doc_type") in preferred:
            return base + DOMAIN_BOOST
        return base

    return sorted(documents, key=boosted_score, reverse=True)
