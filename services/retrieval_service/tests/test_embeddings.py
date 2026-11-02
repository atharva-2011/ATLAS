"""Unit tests for embedding providers."""

import pytest
from retrieval_service.core.config import Settings
from retrieval_service.embeddings.factory import get_embedding_provider
from retrieval_service.embeddings.local import DeterministicLocalEmbeddingProvider


def test_deterministic_local_embedding_provider_initialization() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=128, model_name="test-embed-128")
    assert provider.dimension == 128
    assert provider.model_name == "test-embed-128"


def test_deterministic_embedding_dimension_and_normalization() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=256)
    vec = provider.embed_text("ATLAS multi-agent research intelligence system")
    assert len(vec) == 256
    # Compute L2 norm
    norm_sq = sum(v * v for v in vec)
    assert pytest.approx(norm_sq, abs=1e-5) == 1.0


def test_deterministic_embedding_determinism() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=384)
    text = "Zero-hallucination verification is paramount."
    vec1 = provider.embed_text(text)
    vec2 = provider.embed_text(text)
    assert vec1 == vec2


def test_deterministic_embedding_empty_string() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=64)
    vec = provider.embed_text("")
    assert len(vec) == 64
    assert vec[0] == 1.0
    assert sum(vec[1:]) == 0.0


def test_deterministic_embedding_batch() -> None:
    provider = DeterministicLocalEmbeddingProvider(dimension=128)
    texts = ["First document paragraph", "Second paragraph about machine learning"]
    batch = provider.embed_batch(texts)
    assert len(batch) == 2
    assert len(batch[0]) == 128
    assert len(batch[1]) == 128


def test_embedding_factory() -> None:
    settings = Settings(embedding_provider="deterministic", vector_dimension=128)
    provider = get_embedding_provider(settings)
    assert provider.dimension == 128
    assert isinstance(provider, DeterministicLocalEmbeddingProvider)
