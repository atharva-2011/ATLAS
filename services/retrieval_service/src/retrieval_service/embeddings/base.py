"""Abstract embedding provider protocol."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol that all embedding providers must implement."""

    @property
    def dimension(self) -> int:
        """Vector embedding dimension length."""
        ...

    @property
    def model_name(self) -> str:
        """Name of the embedding model."""
        ...

    def embed_text(self, text: str) -> list[float]:
        """Generate normalized embedding vector for a single string.

        Args:
            text: Text to embed.

        Returns:
            Normalized list of floats of length `dimension`.
        """
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate normalized embeddings for multiple strings.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors.
        """
        ...
