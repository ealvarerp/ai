import hashlib

from app.config import Settings
from app.models import QueryRequest, QueryResponse
from app.query.content_safety import ContentSafetyService
from app.query.hybrid_search import HybridSearchService
from app.query.response_generator import ResponseGenerator
from app.storage.redis_cache import RedisCache
from app.storage.sql_audit import SqlAudit


class RagQueryService:
    def __init__(
        self,
        hybrid_search: HybridSearchService,
        response_generator: ResponseGenerator,
        content_safety: ContentSafetyService,
        cache: RedisCache,
        audit: SqlAudit,
        settings: Settings,
    ):
        self.hybrid_search = hybrid_search
        self.response_generator = response_generator
        self.content_safety = content_safety
        self.cache = cache
        self.audit = audit
        self.settings = settings

    def query(self, request: QueryRequest) -> QueryResponse:
        cache_key = "query:" + hashlib.sha256(
            f"{request.query}:{request.top_k}".encode("utf-8")
        ).hexdigest()

        cached = self.cache.get_json(cache_key)
        if cached:
            return QueryResponse(
                answer=cached.get("answer", ""),
                citations=cached.get("citations", []),
                cache_hit=True,
            )

        self.content_safety.check_text(request.query, direction="input")

        self.audit.log(
            document_id="query",
            stage="query.received",
            status="info",
            details={"query": request.query, "top_k": request.top_k},
        )

        chunks = self.hybrid_search.search(
            query=request.query,
            top_k=request.top_k or self.settings.query_top_k,
        )

        answer, citations = self.response_generator.generate(
            query=request.query,
            chunks=chunks,
        )

        self.content_safety.check_text(answer, direction="output")

        response = QueryResponse(
            answer=answer,
            citations=citations,
            cache_hit=False,
        )

        self.cache.set_json(
            cache_key,
            response.model_dump(),
            ttl_seconds=self.settings.cache_ttl_seconds,
        )

        return response
