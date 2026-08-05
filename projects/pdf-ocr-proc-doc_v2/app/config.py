from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None

    blob_account_url: str
    blob_container: str = "pdf-documents"

    search_endpoint: str
    search_api_key: str | None = None
    search_index: str = "pdf-rag-index"

    cosmos_endpoint: str
    cosmos_database: str = "pdf-rag"
    cosmos_container: str = "document-metadata"

    sql_connection_string: str = "sqlite:///./audit.db"
    redis_url: str = "redis://localhost:6379/0"

    doc_intelligence_endpoint: str
    doc_intelligence_key: str | None = None

    openai_endpoint: str
    openai_api_key: str | None = None
    openai_api_version: str = "2024-10-21"
    embedding_deployment: str = "text-embedding-3-small"
    chat_deployment: str = "gpt-4o"

    content_safety_endpoint: str | None = None
    content_safety_key: str | None = None

    max_chunk_tokens: int = 800
    max_pages_per_batch: int = 25
    min_ocr_confidence: float = 0.75
    query_top_k: int = 8
    cache_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PDF_RAG_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
