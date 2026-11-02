"""Embeddings package for Retrieval Service."""

from retrieval_service.embeddings.base import EmbeddingProvider
from retrieval_service.embeddings.factory import get_embedding_provider
from retrieval_service.embeddings.local import DeterministicLocalEmbeddingProvider

__all__ = [
    "DeterministicLocalEmbeddingProvider",
    "EmbeddingProvider",
    "get_embedding_provider",
]
