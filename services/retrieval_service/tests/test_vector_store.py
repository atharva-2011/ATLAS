"""Unit and integration tests for Qdrant vector store adapter and indexing/search API."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from qdrant_client import AsyncQdrantClient
from retrieval_service.core.config import Settings
from retrieval_service.embeddings.local import DeterministicLocalEmbeddingProvider
from retrieval_service.main import create_app
from retrieval_service.vector_store.qdrant_adapter import QdrantVectorStoreAdapter


@pytest.mark.anyio
async def test_qdrant_adapter_index_and_search() -> None:
    settings = Settings(
        qdrant_location=":memory:",
        collection_name="test_collection_lifecycle",
        vector_dimension=128,
    )
    provider = DeterministicLocalEmbeddingProvider(dimension=128)
    client = AsyncQdrantClient(location=":memory:")
    adapter = QdrantVectorStoreAdapter(
        settings=settings,
        embedding_provider=provider,
        client=client,
    )

    tenant_id = "tenant-alpha"
    doc_id = uuid4()
    chunks = [
        {
            "chunk_index": 0,
            "text": "ATLAS implements multi-agent automated research workflows.",
            "content_hash": "hash-001",
            "locator": {"page": 1, "paragraph": 1},
        },
        {
            "chunk_index": 1,
            "text": "Every factual claim must be backed by traceable evidence snippets.",
            "content_hash": "hash-002",
            "locator": {"page": 1, "paragraph": 2},
        },
    ]

    result = await adapter.index_chunks(
        tenant_id=tenant_id,
        document_id=doc_id,
        chunks=chunks,
    )

    assert result.indexed_count == 2
    assert result.tenant_id == tenant_id
    assert result.document_id == doc_id

    # Search for claims in tenant-alpha
    results = await adapter.search(
        tenant_id=tenant_id,
        query="factual claim evidence verification",
        top_k=2,
    )

    assert len(results) > 0
    assert results[0].document_id == doc_id
    assert results[0].tenant_id == tenant_id
    assert "claim" in results[0].text or "evidence" in results[0].text
    assert 0.0 <= results[0].score <= 1.0

    await adapter.close()


@pytest.mark.anyio
async def test_qdrant_adapter_strict_tenant_isolation() -> None:
    settings = Settings(
        qdrant_location=":memory:",
        collection_name="test_tenant_isolation",
        vector_dimension=128,
    )
    provider = DeterministicLocalEmbeddingProvider(dimension=128)
    client = AsyncQdrantClient(location=":memory:")
    adapter = QdrantVectorStoreAdapter(
        settings=settings,
        embedding_provider=provider,
        client=client,
    )

    doc_a = uuid4()
    doc_b = uuid4()

    # Index into Tenant A
    await adapter.index_chunks(
        tenant_id="tenant-A",
        document_id=doc_a,
        chunks=[{"chunk_index": 0, "text": "Confidential financial quarterly earnings for Corp A"}],
    )

    # Index into Tenant B
    await adapter.index_chunks(
        tenant_id="tenant-B",
        document_id=doc_b,
        chunks=[{"chunk_index": 0, "text": "Public engineering notes for Corp B"}],
    )

    # Search with Tenant A - must NEVER return Tenant B data
    results_a = await adapter.search(
        tenant_id="tenant-A",
        query="financial earnings",
        top_k=5,
    )
    assert len(results_a) == 1
    assert results_a[0].tenant_id == "tenant-A"
    assert results_a[0].document_id == doc_a

    # Search with Tenant B for financial earnings:
    # Qdrant will retrieve up to top_k matching Tenant B points, but must NEVER leak Tenant A data!
    results_b = await adapter.search(
        tenant_id="tenant-B",
        query="financial earnings",
        top_k=5,
    )
    # Crucial tenant isolation guarantee: No result from tenant-A may ever appear!
    assert all(r.tenant_id == "tenant-B" for r in results_b)
    assert not any(r.document_id == doc_a for r in results_b)

    await adapter.close()


@pytest.mark.anyio
async def test_retrieval_service_api_endpoints() -> None:
    settings = Settings(
        qdrant_location=":memory:",
        collection_name=f"test_api_{uuid4().hex[:8]}",
        vector_dimension=64,
    )
    app = create_app(settings=settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        doc_id = str(uuid4())
        index_payload = {
            "tenant_id": "test-tenant-123",
            "document_id": doc_id,
            "chunks": [
                {
                    "chunk_index": 0,
                    "text": "The quick brown fox jumps over the lazy dog.",
                    "content_hash": "hash-fox",
                    "locator": {"page": 1},
                }
            ],
        }

        # Index chunk
        index_res = await client.post("/api/v1/retrieval/index-chunks", json=index_payload)
        assert index_res.status_code == 201
        data = index_res.json()
        assert data["indexed_count"] == 1
        assert data["tenant_id"] == "test-tenant-123"

        # Search matching query
        search_payload = {
            "tenant_id": "test-tenant-123",
            "query": "quick brown fox",
            "top_k": 3,
        }
        search_res = await client.post("/api/v1/retrieval/search", json=search_payload)
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert search_data["results_count"] == 1
        assert "fox" in search_data["results"][0]["text"]
