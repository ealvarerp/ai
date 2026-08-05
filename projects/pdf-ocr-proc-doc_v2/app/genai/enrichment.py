import json

from app.genai.azure_openai import ChatService


def _parse_json(text: str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        text = text.removeprefix("```json")
        text = text.removeprefix("```")
        text = text.removesuffix("```")

    try:
        return json.loads(text.strip())
    except Exception:
        return {}


class Summarizer:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    def summarize(self, text: str) -> str:
        if not text.strip():
            return ""

        truncated = text[:12000]

        messages = [
            {
                "role": "system",
                "content": "You are a document summarization assistant. Summarize the document accurately and concisely.",
            },
            {
                "role": "user",
                "content": f"Summarize the following document:\n\n{truncated}",
            },
        ]

        return self.chat_service.complete(messages, temperature=0.2)


class EntityExtractor:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    def extract(self, text: str) -> list[dict]:
        if not text.strip():
            return []

        truncated = text[:12000]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an entity extraction assistant. "
                    "Return only valid JSON. "
                    "Use this schema: "
                    '{"entities":[{"text":"entity value","label":"PERSON|ORGANIZATION|LOCATION|DATE|MONEY|PRODUCT|OTHER"}]}'
                ),
            },
            {
                "role": "user",
                "content": f"Extract entities from this text:\n\n{truncated}",
            },
        ]

        response = self.chat_service.complete(messages, temperature=0.0)
        parsed = _parse_json(response)

        entities = parsed.get("entities", [])
        if isinstance(entities, list):
            return entities

        return []


class DocumentClassifier:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    def classify(self, text: str) -> dict:
        if not text.strip():
            return {
                "document_type": "unknown",
                "confidence": 0.0,
            }

        truncated = text[:12000]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a document classification assistant. "
                    "Return only valid JSON. "
                    "Use this schema: "
                    '{"document_type":"invoice|contract|report|policy|manual|correspondence|form|other","confidence":0.0}'
                ),
            },
            {
                "role": "user",
                "content": f"Classify this document:\n\n{truncated}",
            },
        ]

        response = self.chat_service.complete(messages, temperature=0.0)
        parsed = _parse_json(response)

        return {
            "document_type": parsed.get("document_type", "unknown"),
            "confidence": parsed.get("confidence", 0.0),
        }
