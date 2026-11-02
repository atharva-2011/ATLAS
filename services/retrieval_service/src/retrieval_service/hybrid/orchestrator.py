"""Hybrid search orchestrator fusing dense vector search and sparse BM25 retrieval.

Implements Reciprocal Rank Fusion (RRF) and linear score interpolation:
    RRF_score(d) = sum( weight / (k + rank(d)) )
"""

from typing import Any
from uuid import UUID

from atlas_contracts.retrieval import (
    HybridSearchItem,
    HybridSearchRequest,
    HybridSearchResponse,
)

from retrieval_service.sparse.bm25_store import BM25Store
from retrieval_service.vector_store.qdrant_adapter import QdrantVectorStoreAdapter


class HybridRetrievalOrchestrator:
    """Coordinates parallel dense and sparse search and fuses results with RRF."""

    def __init__(
        self,
        vector_store: QdrantVectorStoreAdapter,
        bm25_store: BM25Store,
    ) -> None:
        self.vector_store = vector_store
        self.bm25_store = bm25_store

    async def search(self, request: HybridSearchRequest) -> HybridSearchResponse:
        """Execute hybrid search using Reciprocal Rank Fusion."""
        # 1. Dense vector search
        dense_results = await self.vector_store.search(
            tenant_id=request.tenant_id,
            query=request.query,
            top_k=request.top_k * 2,  # Fetch wider candidate pool
            document_id=request.document_id,
        )

        # 2. Sparse BM25 search
        sparse_results = self.bm25_store.search(
            tenant_id=request.tenant_id,
            query=request.query,
            top_k=request.top_k * 2,
            document_id=request.document_id,
        )

        # 3. Fuse with Reciprocal Rank Fusion (RRF)
        # Unique item identified by (document_id, chunk_index) or chunk text
        fused_scores: dict[str, float] = {}
        items_by_key: dict[str, dict[str, Any]] = {}

        dense_ranks: dict[str, int] = {}
        dense_scores: dict[str, float] = {}
        for rank, d_item in enumerate(dense_results, start=1):
            key = f"{d_item.document_id}:{d_item.chunk_index}"
            dense_ranks[key] = rank
            dense_scores[key] = d_item.score
            rrf_val = request.dense_weight * (1.0 / (request.rrf_k + rank))
            fused_scores[key] = fused_scores.get(key, 0.0) + rrf_val
            items_by_key[key] = {
                "chunk_id": d_item.chunk_id,
                "document_id": d_item.document_id,
                "chunk_index": d_item.chunk_index,
                "text": d_item.text,
                "locator": d_item.locator,
                "tenant_id": d_item.tenant_id,
            }

        sparse_ranks: dict[str, int] = {}
        sparse_scores: dict[str, float] = {}
        for rank, s_item in enumerate(sparse_results, start=1):
            key = f"{s_item['document_id']}:{s_item['chunk_index']}"
            sparse_ranks[key] = rank
            sparse_scores[key] = s_item["score"]
            rrf_val = request.sparse_weight * (1.0 / (request.rrf_k + rank))
            fused_scores[key] = fused_scores.get(key, 0.0) + rrf_val
            if key not in items_by_key:
                items_by_key[key] = {
                    "chunk_id": s_item["chunk_id"],
                    "document_id": s_item["document_id"],
                    "chunk_index": s_item["chunk_index"],
                    "text": s_item["text"],
                    "locator": s_item["locator"],
                    "tenant_id": s_item["tenant_id"],
                }

        # 4. Sort and build final ranked items
        sorted_keys = sorted(fused_scores.keys(), key=lambda k: fused_scores[k], reverse=True)

        # Theoretical max RRF score for normalization to [0, 1]
        max_theoretical_rrf = (request.dense_weight + request.sparse_weight) * (
            1.0 / (request.rrf_k + 1)
        )
        scale = max_theoretical_rrf if max_theoretical_rrf > 0 else 1.0

        hybrid_items: list[HybridSearchItem] = []
        for key in sorted_keys[: request.top_k]:
            meta = items_by_key[key]
            raw_score = fused_scores[key]
            normalized_score = min(1.0, max(0.0, raw_score / scale))

            doc_id_val = meta["document_id"]
            doc_uuid = doc_id_val if isinstance(doc_id_val, UUID) else UUID(str(doc_id_val))

            hybrid_items.append(
                HybridSearchItem(
                    chunk_id=meta["chunk_id"],
                    document_id=doc_uuid,
                    chunk_index=meta["chunk_index"],
                    text=meta["text"],
                    locator=meta["locator"],
                    combined_score=normalized_score,
                    dense_score=dense_scores.get(key),
                    sparse_score=sparse_scores.get(key),
                    dense_rank=dense_ranks.get(key),
                    sparse_rank=sparse_ranks.get(key),
                    tenant_id=meta["tenant_id"],
                )
            )

        return HybridSearchResponse(
            query=request.query,
            tenant_id=request.tenant_id,
            results_count=len(hybrid_items),
            results=hybrid_items,
        )
