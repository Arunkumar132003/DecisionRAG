import re

# Patterns that match real or fake secrets in document text
_SECRET_PATTERNS = [
    (re.compile(r'sk_live_[A-Za-z0-9]{10,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'sk_test_[A-Za-z0-9]{10,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'pk_live_[A-Za-z0-9]{10,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'AIza[A-Za-z0-9_\-]{35,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'ghp_[A-Za-z0-9]{36,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'(?:password|passwd|secret|api[_\s]?key|token|oauth|private[_\s]?key)\s*[:=]\s*\S+', re.IGNORECASE), '[REDACTED_SECRET]'),
    (re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b'), '[REDACTED_CARD]'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[REDACTED_SSN]'),
    (re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}'), '[REDACTED_EMAIL]'),
    (re.compile(r'\bT-\d{4,}\b'), '[REDACTED_EMPLOYEE_ID]'),
]

# Questions that are themselves asking for secrets — block before retrieval
_SENSITIVE_REQUEST_PATTERNS = re.compile(
    r'\b(api[_\s]?key|api[_\s]?token|access[_\s]?token|oauth[_\s]?token|secret[_\s]?key|'
    r'private[_\s]?key|credential|password|passwd|bearer[_\s]?token|auth[_\s]?token|'
    r'client[_\s]?secret|webhook[_\s]?secret|signing[_\s]?key|encryption[_\s]?key)\b',
    re.IGNORECASE,
)

BLOCKED_RESPONSE = (
    "I cannot provide API keys, credentials, access tokens, or any secrets. "
    "The documentation may contain example or placeholder values that must never be disclosed. "
    "If you need access credentials, please contact your system administrator or refer to "
    "your organisation's secure secrets management process."
)


def is_sensitive_request(question: str) -> bool:
    """Return True if the question is asking for secrets/credentials."""
    return bool(_SENSITIVE_REQUEST_PATTERNS.search(question))


def redact_context(context: str) -> str:
    """Strip all secret-like values from the context before sending to LLM."""
    for pattern, replacement in _SECRET_PATTERNS:
        context = pattern.sub(replacement, context)
    return context
