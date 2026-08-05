from app.genai.azure_openai import EmbeddingService
from app.models import RetrievedChunk
from app.storage.search_store import SearchStore


class HybridSearchService:
    def __init__(
        self,
        search_store: SearchStore,
        embedding_service: EmbeddingService,
    ):
        self.search_store = search_store
        self.embedding_service = embedding_service

    def search(
        self,
        query: str,
        top_k: int = 8,
    ) -> list[RetrievedChunk]:
        query_embedding = self.embedding_service.embed_text(query)

        return self.search_store.search(
            query=query,
            query_embedding=query_embedding,
            top=top_k,
        )
