from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class IngestedDocument(BaseModel):
    name: str
    content: bytes
    source: str
    metadata: dict[str, Any] = {}


class QueryRequest(BaseModel):
    query: str
    top_k: int = 8


class Citation(BaseModel):
    chunk_id: Optional[str] = None
    source: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None


class RetrievedChunk(BaseModel):
    id: str
    parent_id: Optional[str] = None
    source: Optional[str] = None
    title: Optional[str] = None
    content: str
    chunk_index: Optional[int] = None
    score: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    cache_hit: bool = False


class ProcessingResult(BaseModel):
    document_id: str
    status: str
    chunks_indexed: int = 0
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
