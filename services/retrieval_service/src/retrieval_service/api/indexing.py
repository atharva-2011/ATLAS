from typing import Annotated

from atlas_contracts.retrieval import (
    ChunkIndexRequest,
    ChunkIndexResult,
    HybridSearchRequest,
    HybridSearchResponse,
    VectorSearchRequest,
    VectorSearchResponse,
)
from fastapi import APIRouter, Depends, status
from retrieval_service.core.config import Settings, get_settings
from retrieval_service.embeddings.factory import get_embedding_provider
from retrieval_service.hybrid.orchestrator import HybridRetrievalOrchestrator
from retrieval_service.sparse.bm25_store import BM25Store
from retrieval_service.vector_store.qdrant_adapter import QdrantVectorStoreAdapter

router = APIRouter(prefix="/api/v1/retrieval", tags=["Retrieval"])

# Global adapter and BM25 store instances
_adapter_instance: QdrantVectorStoreAdapter | None = None
_bm25_store_instance: BM25Store | None = None


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


def get_bm25_store() -> BM25Store:
    """Dependency that returns a shared BM25Store."""
    global _bm25_store_instance
    if _bm25_store_instance is None:
        _bm25_store_instance = BM25Store()
    return _bm25_store_instance


def get_hybrid_orchestrator(
    vector_store: Annotated[QdrantVectorStoreAdapter, Depends(get_vector_store)],
    bm25_store: Annotated[BM25Store, Depends(get_bm25_store)],
) -> HybridRetrievalOrchestrator:
    """Dependency returning HybridRetrievalOrchestrator."""
    return HybridRetrievalOrchestrator(
        vector_store=vector_store,
        bm25_store=bm25_store,
    )


@router.post(
    "/index-chunks",
    response_model=ChunkIndexResult,
    status_code=status.HTTP_201_CREATED,
    summary="Index document chunks into vector store and BM25 sparse index",
)
async def index_document_chunks(
    payload: ChunkIndexRequest,
    vector_store: Annotated[QdrantVectorStoreAdapter, Depends(get_vector_store)],
    bm25_store: Annotated[BM25Store, Depends(get_bm25_store)],
) -> ChunkIndexResult:
    """Vectorize into Qdrant and index into BM25 with strict tenant partitioning."""
    # Index in BM25 store
    bm25_store.index_chunks(
        tenant_id=payload.tenant_id,
        document_id=payload.document_id,
        chunks=payload.chunks,
    )

    # Index in vector store
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


@router.post(
    "/hybrid-search",
    response_model=HybridSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute hybrid retrieval fusing dense vectors and BM25",
)
async def search_hybrid(
    payload: HybridSearchRequest,
    hybrid_orchestrator: Annotated[HybridRetrievalOrchestrator, Depends(get_hybrid_orchestrator)],
) -> HybridSearchResponse:
    """Retrieve top-K hybrid ranked chunks with reciprocal rank fusion."""
    return await hybrid_orchestrator.search(payload)
