from dataclasses import dataclass
from typing import Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    DocumentContentFormat,
)
from azure.core.credentials import AzureKeyCredential

from app.config import Settings
from app.security.credentials import get_azure_token_credential


@dataclass
class DocumentIntelligenceResult:
    content: str
    tables: list[Any]
    figures: list[Any]
    pages: list[Any]
    raw: Any


class AzureDocumentIntelligenceService:
    def __init__(self, settings: Settings):
        if settings.doc_intelligence_key:
            credential = AzureKeyCredential(settings.doc_intelligence_key)
        else:
            credential = get_azure_token_credential(settings)

        self.client = DocumentIntelligenceClient(
            endpoint=settings.doc_intelligence_endpoint,
            credential=credential,
        )

    def analyze(self, pdf_bytes: bytes) -> DocumentIntelligenceResult:
        request = AnalyzeDocumentRequest(bytes_source=pdf_bytes)

        poller = self.client.begin_analyze_document(
            model_id="prebuilt-layout",
            analyze_request=request,
            output_content_format=DocumentContentFormat.MARKDOWN,
        )

        result = poller.result()

        return DocumentIntelligenceResult(
            content=getattr(result, "content", "") or "",
            tables=list(getattr(result, "tables", []) or []),
            figures=list(getattr(result, "figures", []) or []),
            pages=list(getattr(result, "pages", []) or []),
            raw=result,
        )
