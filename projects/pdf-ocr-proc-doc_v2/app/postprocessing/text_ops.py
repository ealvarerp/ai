import re
import unicodedata
from datetime import datetime
from typing import Any

from langdetect import detect

from app.document_intelligence.azure_di import DocumentIntelligenceResult
from app.storage.cosmos_store import CosmosStore


class TextNormalizer:
    def normalize(self, text: str) -> str:
        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\x00", "")
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()


class LanguageDetector:
    def detect(self, text: str) -> str:
        if not text or not text.strip():
            return "unknown"

        try:
            return detect(text[:5000])
        except Exception:
            return "unknown"


class ConfidenceScorer:
    def score(self, result: DocumentIntelligenceResult) -> float:
        confidences: list[float] = []

        for page in result.pages:
            confidence = getattr(page, "confidence", None)
            if confidence is not None:
                try:
                    confidences.append(float(confidence))
                except Exception:
                    continue

        if confidences:
            return sum(confidences) / len(confidences)

        if len(result.content.strip()) > 200:
            return 0.85

        return 0.55


class HitlQueue:
    """
    Human-in-the-loop validation queue.

    Stores low-confidence documents in Cosmos DB for manual review.
    """

    def __init__(self, cosmos_store: CosmosStore):
        self.cosmos_store = cosmos_store

    def enqueue(
        self,
        document_id: str,
        reason: str,
        content_snippet: str,
        source: str,
    ) -> None:
        item = {
            "id": f"hitl-{document_id}",
            "parent_id": document_id,
            "partition_key": document_id,
            "type": "hitl_validation",
            "document_id": document_id,
            "source": source,
            "reason": reason,
            "content_snippet": content_snippet[:2000],
            "status": "pending_review",
            "created_at": datetime.utcnow().isoformat(),
        }

        self.cosmos_store.upsert_document_metadata(item)


class MetadataExtractor:
    def extract(
        self,
        pdf_bytes: bytes,
        text: str,
        source: str,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "source": source,
        }

        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(pdf_bytes))

            if reader.metadata:
                if reader.metadata.author:
                    metadata["author"] = reader.metadata.author

                if reader.metadata.title:
                    metadata["title"] = reader.metadata.title

                if reader.metadata.subject:
                    metadata["subject"] = reader.metadata.subject

                if reader.metadata.creator:
                    metadata["creator"] = reader.metadata.creator

                if reader.metadata.producer:
                    metadata["producer"] = reader.metadata.producer

        except Exception:
            pass

        emails = list(set(re.findall(r"[\w\.-]+@[\w\.-]+", text or "")))
        if emails:
            metadata["emails"] = emails[:25]

        dates = list(
            set(
                re.findall(
                    r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b",
                    text or "",
                )
            )
        )

        if dates:
            metadata["dates"] = dates[:25]

        return metadata
