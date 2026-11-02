"""BM25 sparse indexer partitioned strictly by tenant."""

import re
from typing import Any
from uuid import UUID

from rank_bm25 import BM25L


def tokenize(text: str) -> list[str]:
    """Lowercase tokenization removing punctuation."""
    return re.findall(r"\b\w+\b", text.lower())


class TenantBM25Index:
    """In-memory BM25 index supporting document chunk storage and keyword scoring."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.chunks: list[dict[str, Any]] = []
        self.tokenized_corpus: list[list[str]] = []
        self.bm25: BM25L | None = None

    def add_chunks(self, document_id: UUID, chunks: list[dict[str, Any]]) -> int:
        """Add chunks to index and rebuild BM25 index structure."""
        for c in chunks:
            record = {
                "chunk_id": c.get("chunk_id") or str(c.get("id", "")),
                "document_id": document_id,
                "chunk_index": c.get("chunk_index", 0),
                "text": c.get("text", ""),
                "locator": c.get("locator", {}),
                "content_hash": c.get("content_hash", ""),
                "tenant_id": self.tenant_id,
            }
            tokens = tokenize(record["text"])
            self.chunks.append(record)
            self.tokenized_corpus.append(tokens)

        if self.tokenized_corpus:
            self.bm25 = BM25L(self.tokenized_corpus)

        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Search BM25 sparse index returning ranked records with BM25 scores."""
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Pair scores with chunk metadata
        indexed_scores = []
        for idx, score in enumerate(scores):
            if score <= 0.0:
                continue
            chunk = self.chunks[idx]
            if document_id is not None and chunk["document_id"] != document_id:
                continue
            indexed_scores.append((score, chunk))

        # Sort descending by BM25 score
        indexed_scores.sort(key=lambda x: x[0], reverse=True)

        results: list[dict[str, Any]] = []
        for rank, (score, chunk) in enumerate(indexed_scores[:top_k], start=1):
            item = dict(chunk)
            item["score"] = float(score)
            item["rank"] = rank
            results.append(item)

        return results


class BM25Store:
    """Tenant-partitioned registry of BM25 indexes."""

    def __init__(self) -> None:
        self._tenants: dict[str, TenantBM25Index] = {}

    def get_or_create(self, tenant_id: str) -> TenantBM25Index:
        if tenant_id not in self._tenants:
            self._tenants[tenant_id] = TenantBM25Index(tenant_id)
        return self._tenants[tenant_id]

    def index_chunks(
        self,
        tenant_id: str,
        document_id: UUID,
        chunks: list[dict[str, Any]],
    ) -> int:
        idx = self.get_or_create(tenant_id)
        return idx.add_chunks(document_id, chunks)

    def search(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
        document_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        if tenant_id not in self._tenants:
            return []
        return self._tenants[tenant_id].search(query, top_k=top_k, document_id=document_id)
