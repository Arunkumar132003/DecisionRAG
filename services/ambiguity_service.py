import re

VAGUE_POLICY_PATTERN = re.compile(
    r"^what\s+is\s+.{0,20}(current\s+)?policy\s*\??$", re.IGNORECASE
)

VAGUE_PATTERNS = [
    re.compile(r"^tell me about\s+(it|this|that|the\s+\w+)\s*\??$", re.IGNORECASE),
    re.compile(r"^what does .{0,15} (say|think|do)\s*\??$", re.IGNORECASE),
    re.compile(r"^how does .{0,15} (work|handle|manage)\s*\??$", re.IGNORECASE),
    re.compile(r"^what (are|is) (the\s+)?(policies|rules|guidelines)\s*\??$", re.IGNORECASE),
]

POLICY_DOMAINS = ["security", "ai", "privacy", "data protection", "usage", "access"]

CLARIFICATION_MESSAGES = {
    "policy": (
        "Your question mentions 'policy' but does not specify which area. "
        "Please clarify which policy you are asking about: "
        "Security Policy, AI Usage Policy, Data Protection, Privacy, or another area."
    ),
    "vague": (
        "Your question is too broad to answer accurately. "
        "Please provide more specific details about what you want to know."
    ),
}


class AmbiguityService:
    """Heuristic-based ambiguity detection — no extra LLM call."""

    def check(self, question: str) -> tuple[bool, str]:
        """
        Returns (is_ambiguous, clarification_message).
        clarification_message is empty if not ambiguous.
        """
        stripped = question.strip()

        if VAGUE_POLICY_PATTERN.match(stripped):
            mentioned = [d for d in POLICY_DOMAINS if d in stripped.lower()]
            if not mentioned:
                return True, CLARIFICATION_MESSAGES["policy"]

        for pattern in VAGUE_PATTERNS:
            if pattern.match(stripped):
                return True, CLARIFICATION_MESSAGES["vague"]

        words = stripped.split()
        if len(words) <= 3:
            return True, (
                f"Your question '{stripped}' is too brief. "
                "Please provide more context so I can give an accurate answer."
            )

        return False, ""
