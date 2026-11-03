"""Contracts and evaluation schemas for Evidence Verification, Citation Faithfulness, and Provenance."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def get_utc_now() -> datetime:
    return datetime.now(UTC)


class ClaimSupportStatus(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"


class NormalizedClaim(BaseModel):
    """Normalized atomic factual claim extracted from text or research report."""

    claim_id: str = Field(default_factory=lambda: f"claim_{uuid4().hex[:6]}")
    text: str = Field(min_length=3, description="Atomic factual assertion")
    is_opinion_or_analysis: bool = False
    cited_evidence_ids: list[str] = Field(default_factory=list)


class ClaimVerificationRequest(BaseModel):
    """Request payload to verify a set of claims against reference passages."""

    tenant_id: str = "default"
    claims: list[NormalizedClaim] = Field(..., min_length=1)
    passages: list[dict[str, Any]] = Field(..., min_length=1)
    strict_provenance: bool = True


class ClaimVerificationRecord(BaseModel):
    """Evaluation result for an individual claim against its referenced evidence."""

    claim_id: str
    claim_text: str
    status: ClaimSupportStatus
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradiction_text: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance_locator: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""


class CitationVerificationRequest(BaseModel):
    """Payload to evaluate a synthesized research report's citation fidelity and grounding."""

    tenant_id: str = "default"
    report_title: str
    report_markdown: str
    referenced_evidence: list[dict[str, Any]] = Field(default_factory=list)


class CitationVerificationResult(BaseModel):
    """Faithfulness and grounding benchmark metrics for synthesized research."""

    total_citations: int
    resolved_citations: int
    unresolved_citations: list[str] = Field(default_factory=list)
    faithfulness_score: float = Field(..., ge=0.0, le=1.0)
    citation_precision: float = Field(..., ge=0.0, le=1.0)
    claims_evaluated: int
    supported_claims_count: int
    contradicted_claims_count: int
    unsupported_claims_count: int
    records: list[ClaimVerificationRecord] = Field(default_factory=list)


class RetrievalQueryEvaluation(BaseModel):
    """Detailed ranking evaluation metrics for an individual test query."""

    query_id: str
    query: str
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    relevant_chunk_ids: list[str] = Field(default_factory=list)
    recall_at_k: dict[int, float] = Field(default_factory=dict)
    reciprocal_rank: float = Field(default=0.0, ge=0.0, le=1.0)
    ndcg_at_k: dict[int, float] = Field(default_factory=dict)
    precision_at_k: dict[int, float] = Field(default_factory=dict)


class RetrievalBenchmarkScorecard(BaseModel):
    """Aggregated retrieval benchmark scorecard across a gold dataset."""

    benchmark_name: str = "ATLAS Retrieval Benchmark"
    total_queries: int
    mean_recall_at_k: dict[int, float] = Field(default_factory=dict)
    mrr: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_ndcg_at_k: dict[int, float] = Field(default_factory=dict)
    mean_precision_at_k: dict[int, float] = Field(default_factory=dict)
    per_query_results: list[RetrievalQueryEvaluation] = Field(default_factory=list)
    relative_lift: dict[str, float] = Field(default_factory=dict)

