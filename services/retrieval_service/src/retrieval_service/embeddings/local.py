"""Deterministic, lightweight local embedding provider.

Designed specifically for host environments with constrained RAM (e.g. 8 GB Windows)
without requiring PyTorch/CUDA wheels. Uses character n-gram hashing and projection
to produce deterministic, normalized cosine-comparable embeddings.
"""

import hashlib
import math

from retrieval_service.embeddings.base import EmbeddingProvider


class DeterministicLocalEmbeddingProvider(EmbeddingProvider):
    """Produces deterministic, normalized pseudo-embeddings of a configured dimension.

    Semantic text similarity is approximated via character 3-gram and 4-gram feature hashing,
    projected into an N-dimensional hypersphere and L2-normalized.
    """

    def __init__(self, dimension: int = 384, model_name: str = "deterministic-local-384") -> None:
        if dimension <= 0:
            msg = "Dimension must be greater than 0"
            raise ValueError(msg)
        self._dimension = dimension
        self._model_name = model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> list[float]:
        if not text.strip():
            # Return zero-like normalized unit vector on dimension 0
            vec = [0.0] * self._dimension
            vec[0] = 1.0
            return vec

        cleaned = text.lower().strip()
        vec = [0.0] * self._dimension

        # 1. Word tokens and character n-grams hashing
        tokens = cleaned.split()
        features: list[str] = list(tokens)
        for token in tokens:
            for n in (3, 4):
                if len(token) >= n:
                    features.extend(token[i : i + n] for i in range(len(token) - n + 1))

        for feat in features:
            h = hashlib.sha256(feat.encode("utf-8")).digest()
            # Pick bucket and sign
            bucket = int.from_bytes(h[:4], byteorder="little") % self._dimension
            sign = 1.0 if (h[4] % 2 == 0) else -1.0
            vec[bucket] += sign

        # 2. L2 normalize vector
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            return [v / norm for v in vec]
        vec[0] = 1.0
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
