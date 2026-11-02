"""Vector indexing and search endpoints for Retrieval Service."""

from typing import Annotated

from atlas_contracts.retrieval import (
    ChunkIndexRequest,
    ChunkIndexResult,
    VectorSearchRequest,
    VectorSearchResponse,
)
from fastapi import APIRouter, Depends, status
from retrieval_service.core.config import Settings, get_settings
from retrieval_service.embeddings.factory import get_embedding_provider
from retrieval_service.vector_store.qdrant_adapter import QdrantVectorStoreAdapter

router = APIRouter(prefix="/api/v1/retrieval", tags=["Retrieval"])

# Global adapter cache per settings instance
_adapter_instance: QdrantVectorStoreAdapter | None = None


def get_vector_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> QdrantVectorStoreAdapter:
    """Dependency that returns a shared QdrantVectorStoreAdapter."""
    global _adapter_instance
    if _adapter_instance is None:
        embedding_provider = get_embedding_provider(settings)
        _adapter_instance = QdrantVectorStoreAdapter(
            settings=settings,
            embedding_provider=embedding_provider,
        )
    return _adapter_instance


@router.post(
    "/index-chunks",
    response_model=ChunkIndexResult,
    status_code=status.HTTP_201_CREATED,
    summary="Index document chunks into vector store",
)
async def index_document_chunks(
    payload: ChunkIndexRequest,
    vector_store: Annotated[QdrantVectorStoreAdapter, Depends(get_vector_store)],
) -> ChunkIndexResult:
    """Vectorize and index document chunks with tenant partitioning."""
    return await vector_store.index_chunks(
        tenant_id=payload.tenant_id,
        document_id=payload.document_id,
        chunks=payload.chunks,
    )


@router.post(
    "/search",
    response_model=VectorSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute vector similarity search",
)
async def search_vectors(
    payload: VectorSearchRequest,
    vector_store: Annotated[QdrantVectorStoreAdapter, Depends(get_vector_store)],
) -> VectorSearchResponse:
    """Retrieve top-K matching chunks enforcing tenant boundary."""
    results = await vector_store.search(
        tenant_id=payload.tenant_id,
        query=payload.query,
        top_k=payload.top_k,
        document_id=payload.document_id,
        min_score=payload.min_score,
    )
    return VectorSearchResponse(
        query=payload.query,
        tenant_id=payload.tenant_id,
        results_count=len(results),
        results=results,
    )
