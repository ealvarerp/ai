from app.config import Settings


class ContentSafetyService:
    """
    Basic content safety guard.

    In production, replace or augment this with:
    - Azure AI Content Safety
    - Prompt shield / jailbreak detection
    - PII redaction
    - Domain-specific banned terms
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.banned_terms = [
            "ignore all previous instructions",
            "ignore previous instructions",
            "disregard previous instructions",
            "drop table",
            "delete from",
            "rm -rf",
        ]

    def check_text(self, text: str, direction: str = "input") -> bool:
        if not text:
            return True

        lowered = text.lower()

        for term in self.banned_terms:
            if term in lowered:
                raise ValueError(f"Unsafe or disallowed content detected in {direction}.")

        return True
