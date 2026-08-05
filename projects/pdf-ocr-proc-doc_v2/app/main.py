from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.api.routes_ingest import router as ingest_router
from app.api.routes_query import router as query_router
from app.document_intelligence.azure_di import AzureDocumentIntelligenceService
from app.genai.azure_openai import ChatService, EmbeddingService, create_openai_client
from app.genai.chunker import SemanticChunker
from app.genai.enrichment import DocumentClassifier, EntityExtractor, Summarizer
from app.orchestration.pipeline import IngestionPipeline
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
from app.query.content_safety import ContentSafetyService
from app.query.hybrid_search import HybridSearchService
from app.query.rag_pipeline import RagQueryService
from app.query.response_generator import ResponseGenerator
from app.storage.blob_store import BlobStore
from app.storage.cosmos_store import CosmosStore
from app.storage.redis_cache import RedisCache
from app.storage.search_store import SearchStore
from app.storage.sql_audit import SqlAudit


def build_components(settings: Settings) -> dict:
    audit = SqlAudit(settings.sql_connection_string)

    blob_store = BlobStore(settings)
    search_store = SearchStore(settings)
    cosmos_store = CosmosStore(settings)
    redis_cache = RedisCache(settings.redis_url)

    password_remover = PasswordRemover()
    validator = PdfValidator()
    image_enhancer = ImageEnhancer()
    page_segmenter = PageSegmenter(settings.max_pages_per_batch)

    document_intelligence = AzureDocumentIntelligenceService(settings)

    text_normalizer = TextNormalizer()
    language_detector = LanguageDetector()
    confidence_scorer = ConfidenceScorer()
    hitl_queue = HitlQueue(cosmos_store)
    metadata_extractor = MetadataExtractor()

    openai_client = create_openai_client(settings)
    embedding_service = EmbeddingService(openai_client, settings)
    chat_service = ChatService(openai_client, settings)

    chunker = SemanticChunker(max_tokens=settings.max_chunk_tokens)
    summarizer = Summarizer(chat_service)
    entity_extractor = EntityExtractor(chat_service)
    classifier = DocumentClassifier(chat_service)

    content_safety = ContentSafetyService(settings)
    hybrid_search = HybridSearchService(search_store, embedding_service)
    response_generator = ResponseGenerator(chat_service)

    pipeline = IngestionPipeline(
        settings=settings,
        blob_store=blob_store,
        search_store=search_store,
        cosmos_store=cosmos_store,
        audit=audit,
        password_remover=password_remover,
        validator=validator,
        image_enhancer=image_enhancer,
        page_segmenter=page_segmenter,
        document_intelligence=document_intelligence,
        text_normalizer=text_normalizer,
        language_detector=language_detector,
        confidence_scorer=confidence_scorer,
        hitl_queue=hitl_queue,
        metadata_extractor=metadata_extractor,
        chunker=chunker,
        embeddings=embedding_service,
        summarizer=summarizer,
        entity_extractor=entity_extractor,
        classifier=classifier,
    )

    query_service = RagQueryService(
        hybrid_search=hybrid_search,
        response_generator=response_generator,
        content_safety=content_safety,
        cache=redis_cache,
        audit=audit,
        settings=settings,
    )

    return {
        "settings": settings,
        "search_store": search_store,
        "blob_store": blob_store,
        "pipeline": pipeline,
        "query_service": query_service,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    components = build_components(settings)

    app.state.settings = components["settings"]
    app.state.pipeline = components["pipeline"]
    app.state.query_service = components["query_service"]

    components["blob_store"].ensure_container()
    components["search_store"].ensure_index()

    yield


app = FastAPI(
    title="PDF RAG Pipeline",
    description="End-to-end PDF ingestion, OCR, RAG indexing, and query API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(query_router)


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
