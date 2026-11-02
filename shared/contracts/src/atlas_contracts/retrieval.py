"""Domain contracts and DTOs for retrieval and vector search operations."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkIndexRequest(BaseModel):
    """Payload to index chunks into the vector store."""

    tenant_id: str = Field(default="default", min_length=1)
    document_id: UUID
    chunks: list[dict[str, Any]] = Field(
        ...,
        description="List of chunks (e.g. DocumentChunkDTO dicts with chunk_index, text, content_hash, locator)",
    )


class ChunkIndexResult(BaseModel):
    """Summary result of an indexing operation."""

    document_id: UUID
    indexed_count: int
    collection_name: str
    tenant_id: str


class VectorSearchResultItem(BaseModel):
    """Single item retrieved from vector search."""

    chunk_id: str
    document_id: UUID
    chunk_index: int
    text: str
    locator: dict[str, Any] = Field(default_factory=dict)
    score: float = Field(..., ge=0.0, le=1.0)
    tenant_id: str


class VectorSearchRequest(BaseModel):
    """Query payload for vector similarity retrieval."""

    tenant_id: str = Field(default="default", min_length=1)
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=100)
    document_id: UUID | None = None
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class VectorSearchResponse(BaseModel):
    """Response containing retrieved search items."""

    query: str
    tenant_id: str
    results_count: int
    results: list[VectorSearchResultItem] = Field(default_factory=list)
