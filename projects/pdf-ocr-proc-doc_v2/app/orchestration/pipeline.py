import json
import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import Settings
from app.document_intelligence.azure_di import AzureDocumentIntelligenceService
from app.genai.azure_openai import EmbeddingService
from app.genai.chunker import SemanticChunker
from app.genai.enrichment import DocumentClassifier, EntityExtractor, Summarizer
from app.models import ProcessingResult
from app.postprocessing.text_ops import (
    ConfidenceScorer,
    HitlQueue,
    LanguageDetector,
    MetadataExtractor,
    TextNormalizer,
)
from app.preprocessing.pdf_ops import (
    ImageEnhancer,
    PageSegmenter,
    PasswordRemover,
    PdfValidator,
)
from app.storage.blob_store import BlobStore
from app.storage.cosmos_store import CosmosStore
from app.storage.search_store import SearchStore
from app.storage.sql_audit import SqlAudit


@dataclass
class ChunkDraft:
    text: str
    chunk_index: int
    parent_id: str
    source: str
    title: str
    language: str
    metadata: dict[str, Any]


class IngestionPipeline:
    def __init__(
        self,
        *,
        settings: Settings,
        blob_store: BlobStore,
        search_store: SearchStore,
        cosmos_store: CosmosStore,
        audit: SqlAudit,
        password_remover: PasswordRemover,
        validator: PdfValidator,
        image_enhancer: ImageEnhancer,
        page_segmenter: PageSegmenter,
        document_intelligence: AzureDocumentIntelligenceService,
        text_normalizer: TextNormalizer,
        language_detector: LanguageDetector,
        confidence_scorer: ConfidenceScorer,
        hitl_queue: HitlQueue,
        metadata_extractor: MetadataExtractor,
        chunker: SemanticChunker,
        embeddings: EmbeddingService,
        summarizer: Summarizer,
        entity_extractor: EntityExtractor,
        classifier: DocumentClassifier,
    ):
        self.settings = settings
        self.blob_store = blob_store
        self.search_store = search_store
        self.cosmos_store = cosmos_store
        self.audit = audit

        self.password_remover = password_remover
        self.validator = validator
        self.image_enhancer = image_enhancer
        self.page_segmenter = page_segmenter
        self.document_intelligence = document_intelligence

        self.text_normalizer = text_normalizer
        self.language_detector = language_detector
        self.confidence_scorer = confidence_scorer
        self.hitl_queue = hitl_queue
        self.metadata_extractor = metadata_extractor

        self.chunker = chunker
        self.embeddings = embeddings
        self.summarizer = summarizer
        self.entity_extractor = entity_extractor
        self.classifier = classifier

    def process_pdf(
        self,
        file_name: str,
        pdf_bytes: bytes,
        source: str,
        password: str | None = None,
        document_id: str | None = None,
    ) -> ProcessingResult:
        document_id = document_id or str(uuid.uuid4())

        self.audit.log(
            document_id=document_id,
            stage="ingestion.started",
            status="info",
            details={
                "file_name": file_name,
                "source": source,
            },
        )

        try:
            pdf_bytes = self.password_remover.remove(pdf_bytes, password)

            validation = self.validator.validate(pdf_bytes)
            if not validation.is_valid:
                raise ValueError(validation.error or "Invalid PDF file.")

            blob_name = f"{source}/{document_id}/{file_name}"
            self.blob_store.upload_bytes(blob_name, pdf_bytes)

            parts = self.page_segmenter.split(pdf_bytes)

            text_parts: list[str] = []
            drafts: list[ChunkDraft] = []
            confidences: list[float] = []
            languages: list[str] = []
            extracted_metadata: dict[str, Any] = {}

            global_chunk_index = 0

            for part_index, part in enumerate(parts):
                enhanced_pdf = self.image_enhancer.enhance(part)

                di_result = self.document_intelligence.analyze(enhanced_pdf)

                normalized_text = self.text_normalizer.normalize(di_result.content)
                if not normalized_text.strip():
                    normalized_text = " "

                text_parts.append(normalized_text)

                language = self.language_detector.detect(normalized_text)
                confidence = self.confidence_scorer.score(di_result)

                languages.append(language)
                confidences.append(confidence)

                part_metadata = self.metadata_extractor.extract(
                    pdf_bytes=part,
                    text=normalized_text,
                    source=source,
                )
                extracted_metadata.update(part_metadata)

                if confidence < self.settings.min_ocr_confidence:
                    self.hitl_queue.enqueue(
                        document_id=document_id,
                        reason=f"Low OCR confidence: {confidence:.2f}",
                        content_snippet=normalized_text[:1000],
                        source=source,
                    )

                chunks = self.chunker.chunk(normalized_text)

                for chunk in chunks:
                    drafts.append(
                        ChunkDraft(
                            text=chunk.text,
                            chunk_index=global_chunk_index,
                            parent_id=document_id,
                            source=source,
                            title=file_name,
                            language=language,
                            metadata={
                                "part_index": part_index,
                                "confidence": confidence,
                                "blob_name": blob_name,
                                "token_count": chunk.token_count,
                            },
                        )
                    )
                    global_chunk_index += 1

            full_text = "\n\n".join(text_parts)
            ai_text = full_text[:20000]

            summary = self.summarizer.summarize(ai_text) if ai_text.strip() else ""
            entities = self.entity_extractor.extract(ai_text) if ai_text.strip() else []
            classification = (
                self.classifier.classify(ai_text)
                if ai_text.strip()
                else {"document_type": "unknown", "confidence": 0.0}
            )

            texts = [draft.text for draft in drafts]
            embeddings = self.embeddings.embed_texts(texts) if texts else []

            search_documents = []

            for draft, embedding in zip(drafts, embeddings):
                search_documents.append(
                    {
                        "id": f"{draft.parent_id}-{draft.chunk_index}",
                        "parent_id": draft.parent_id,
                        "source": draft.source,
                        "title": draft.title,
                        "content": draft.text,
                        "chunk_index": draft.chunk_index,
                        "language": draft.language,
                        "metadata": json.dumps(draft.metadata, default=str),
                        "embedding": embedding,
                    }
                )

            self.search_store.upload_chunks(search_documents)

            detected_language = (
                max(set(languages), key=languages.count)
                if languages
                else "unknown"
            )

            document_metadata = {
                "id": document_id,
                "parent_id": document_id,
                "source": source,
                "file_name": file_name,
                "blob_name": blob_name,
                "page_count": validation.page_count,
                "language": detected_language,
                "confidence": statistics.mean(confidences) if confidences else None,
                "document_type": classification.get("document_type", "unknown"),
                "classification_confidence": classification.get("confidence"),
                "summary": summary,
                "entities": entities,
                "extracted_metadata": extracted_metadata,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.cosmos_store.upsert_document_metadata(document_metadata)

            self.audit.log(
                document_id=document_id,
                stage="ingestion.completed",
                status="success",
                details={
                    "chunks_indexed": len(search_documents),
                    "page_count": validation.page_count,
                },
            )

            return ProcessingResult(
                document_id=document_id,
                status="completed",
                chunks_indexed=len(search_documents),
                source=source,
            )

        except Exception as exc:
            self.audit.log(
                document_id=document_id,
                stage="ingestion.failed",
                status="error",
                details={"error": str(exc)},
            )
            raise
