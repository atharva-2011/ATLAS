"""Qdrant vector store adapter providing async indexing, querying, and tenant isolation."""

from typing import Any
from uuid import UUID, uuid4

from atlas_contracts.retrieval import (
    ChunkIndexResult,
    VectorSearchResultItem,
)
from qdrant_client import AsyncQdrantClient, models

from retrieval_service.core.config import Settings
from retrieval_service.embeddings.base import EmbeddingProvider


class QdrantVectorStoreAdapter:
    """Manages collection lifecycles, chunk indexing, and scoped vector searches."""

    def __init__(
        self,
        settings: Settings,
        embedding_provider: EmbeddingProvider,
        client: AsyncQdrantClient | None = None,
    ) -> None:
        self.settings = settings
        self.embedding_provider = embedding_provider
        self.collection_name = settings.collection_name

        if client is not None:
            self.client = client
        elif settings.qdrant_path:
            self.client = AsyncQdrantClient(path=settings.qdrant_path)
        else:
            self.client = AsyncQdrantClient(location=settings.qdrant_location)

    async def ensure_collection(self) -> None:
        """Create the target collection if it does not already exist."""
        collections_response = await self.client.get_collections()
        existing_names = [col.name for col in collections_response.collections]
        if self.collection_name not in existing_names:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_provider.dimension,
                    distance=models.Distance.COSINE,
                ),
            )

    async def index_chunks(
        self,
        tenant_id: str,
        document_id: UUID,
        chunks: list[dict[str, Any]],
    ) -> ChunkIndexResult:
        """Embed and upsert chunks with mandatory tenant metadata and locators.

        Args:
            tenant_id: Tenant partition key.
            document_id: Source document UUID.
            chunks: List of chunk dicts (chunk_index, text, content_hash, locator).

        Returns:
            ChunkIndexResult summary.
        """
        await self.ensure_collection()

        if not chunks:
            return ChunkIndexResult(
                document_id=document_id,
                indexed_count=0,
                collection_name=self.collection_name,
                tenant_id=tenant_id,
            )

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_provider.embed_batch(texts)

        points: list[models.PointStruct] = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings, strict=True)):
            chunk_point_id = str(uuid4())
            payload = {
                "tenant_id": tenant_id,
                "document_id": str(document_id),
                "chunk_index": chunk.get("chunk_index", idx),
                "text": chunk["text"],
                "content_hash": chunk.get("content_hash", ""),
                "locator": chunk.get("locator", {}),
            }
            points.append(
                models.PointStruct(
                    id=chunk_point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        await self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return ChunkIndexResult(
            document_id=document_id,
            indexed_count=len(points),
            collection_name=self.collection_name,
            tenant_id=tenant_id,
        )

    async def search(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
        document_id: UUID | None = None,
        min_score: float = 0.0,
    ) -> list[VectorSearchResultItem]:
        """Perform similarity search with strict tenant isolation filter.

        Args:
            tenant_id: Mandatory tenant isolation identifier.
            query: Query text to embed and search.
            top_k: Maximum number of points to retrieve.
            document_id: Optional filter for specific document scope.
            min_score: Minimum cosine similarity score threshold.

        Returns:
            List of matching VectorSearchResultItem objects.
        """
        await self.ensure_collection()

        query_vector = self.embedding_provider.embed_text(query)

        # Strict tenant isolation filter
        must_filters: list[models.FieldCondition] = [
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=tenant_id),
            )
        ]

        if document_id is not None:
            must_filters.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=str(document_id)),
                )
            )

        query_filter = models.Filter(must=must_filters)

        # qdrant-client >= 1.10 provides client.query_points
        try:
            results = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=min_score if min_score > 0.0 else None,
                with_payload=True,
            )
            points = results.points
        except (AttributeError, TypeError):
            # Fallback for search_points in alternative client versions
            points = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=min_score if min_score > 0.0 else None,
                with_payload=True,
            )

        items: list[VectorSearchResultItem] = []
        for point in points:
            payload = point.payload or {}
            score = float(point.score) if point.score is not None else 0.0
            # Clamp cosine score into [0.0, 1.0]
            normalized_score = max(0.0, min(1.0, score))

            doc_id_val = payload.get("document_id")
            doc_uuid = UUID(doc_id_val) if doc_id_val else uuid4()

            items.append(
                VectorSearchResultItem(
                    chunk_id=str(point.id),
                    document_id=doc_uuid,
                    chunk_index=int(payload.get("chunk_index", 0)),
                    text=str(payload.get("text", "")),
                    locator=payload.get("locator", {}),
                    score=normalized_score,
                    tenant_id=str(payload.get("tenant_id", tenant_id)),
                )
            )

        return items

    async def close(self) -> None:
        """Close underlying client connections."""
        await self.client.close()
