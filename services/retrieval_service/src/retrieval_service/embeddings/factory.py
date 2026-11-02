"""Embedding provider factory."""

from retrieval_service.core.config import Settings
from retrieval_service.embeddings.base import EmbeddingProvider
from retrieval_service.embeddings.local import DeterministicLocalEmbeddingProvider


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Instantiate configured embedding provider based on application settings."""
    provider_type = settings.embedding_provider.lower()
    if provider_type in ("local", "deterministic"):
        return DeterministicLocalEmbeddingProvider(
            dimension=settings.vector_dimension,
            model_name=settings.embedding_model,
        )

    # Fallback to deterministic local provider
    return DeterministicLocalEmbeddingProvider(
        dimension=settings.vector_dimension,
        model_name=settings.embedding_model,
    )
