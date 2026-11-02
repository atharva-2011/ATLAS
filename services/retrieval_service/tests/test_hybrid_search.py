"""Unit and integration tests for BM25 sparse search and hybrid retrieval fusion."""

from uuid import uuid4

import pytest
from atlas_contracts.retrieval import HybridSearchRequest
from httpx import ASGITransport, AsyncClient
from qdrant_client import AsyncQdrantClient
from retrieval_service.core.config import Settings
from retrieval_service.embeddings.local import DeterministicLocalEmbeddingProvider
from retrieval_service.hybrid.orchestrator import HybridRetrievalOrchestrator
from retrieval_service.main import create_app
from retrieval_service.sparse.bm25_store import BM25Store, tokenize
from retrieval_service.vector_store.qdrant_adapter import QdrantVectorStoreAdapter


def test_bm25_tokenizer() -> None:
    tokens = tokenize("ATLAS: Zero-hallucination, high-accuracy RAG!")
    assert "atlas" in tokens
    assert "hallucination" in tokens
    assert "rag" in tokens


def test_bm25_store_and_search() -> None:
    store = BM25Store()
    tenant_id = "tenant-test"
    doc_id = uuid4()
    chunks = [
        {
            "chunk_id": "c1",
            "chunk_index": 0,
            "text": "Deep learning models require validation sets.",
        },
        {
            "chunk_id": "c2",
            "chunk_index": 1,
            "text": "PostgreSQL database handles transactional consistency.",
        },
    ]

    indexed = store.index_chunks(tenant_id, doc_id, chunks)
    assert indexed == 2

    # Query for database
    results = store.search(tenant_id, query="transactional database", top_k=2)
    assert len(results) == 1
    assert results[0]["chunk_id"] == "c2"
    assert results[0]["score"] > 0.0

    # Query with another tenant - should yield 0 results
    empty_results = store.search("tenant-other", query="database", top_k=2)
    assert len(empty_results) == 0


@pytest.mark.anyio
async def test_hybrid_retrieval_fusion() -> None:
    settings = Settings(
        qdrant_location=":memory:",
        collection_name=f"test_hybrid_{uuid4().hex[:8]}",
        vector_dimension=64,
    )
    provider = DeterministicLocalEmbeddingProvider(dimension=64)
    qdrant_client = AsyncQdrantClient(location=":memory:")
    vector_store = QdrantVectorStoreAdapter(settings, provider, qdrant_client)
    bm25_store = BM25Store()

    orchestrator = HybridRetrievalOrchestrator(vector_store, bm25_store)

    tenant_id = "tenant-hybrid"
    doc_id = uuid4()
    chunks = [
        {
            "chunk_id": "c-alpha",
            "chunk_index": 0,
            "text": "Quantum computing utilizes superposition and entanglement states.",
            "locator": {"page": 1},
        },
        {
            "chunk_id": "c-beta",
            "chunk_index": 1,
            "text": "Standard classical algorithms rely on binary logic gates.",
            "locator": {"page": 2},
        },
    ]

    # Index into both stores
    await vector_store.index_chunks(tenant_id, doc_id, chunks)
    bm25_store.index_chunks(tenant_id, doc_id, chunks)

    # Hybrid search
    request = HybridSearchRequest(
        tenant_id=tenant_id,
        query="superposition quantum",
        top_k=2,
        dense_weight=0.5,
        sparse_weight=0.5,
    )
    res = await orchestrator.search(request)

    assert res.results_count > 0
    top_result = res.results[0]
    assert top_result.document_id == doc_id
    assert "quantum" in top_result.text.lower()
    assert 0.0 <= top_result.combined_score <= 1.0

    await vector_store.close()


@pytest.mark.anyio
async def test_hybrid_search_api_endpoint() -> None:
    settings = Settings(
        qdrant_location=":memory:",
        collection_name=f"test_api_hybrid_{uuid4().hex[:8]}",
        vector_dimension=64,
    )
    app = create_app(settings=settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        doc_id = str(uuid4())
        index_payload = {
            "tenant_id": "corp-hybrid",
            "document_id": doc_id,
            "chunks": [
                {
                    "chunk_index": 0,
                    "text": "Revenue growth was driven by cloud enterprise adoption in 2026.",
                    "locator": {"section": "Summary"},
                }
            ],
        }

        # Index
        index_res = await client.post("/api/v1/retrieval/index-chunks", json=index_payload)
        assert index_res.status_code == 201

        # Hybrid Search
        hybrid_req = {
            "tenant_id": "corp-hybrid",
            "query": "cloud enterprise revenue",
            "top_k": 3,
        }
        res = await client.post("/api/v1/retrieval/hybrid-search", json=hybrid_req)
        assert res.status_code == 200
        data = res.json()
        assert data["results_count"] == 1
        assert "cloud" in data["results"][0]["text"].lower()
        assert data["results"][0]["combined_score"] > 0.0
