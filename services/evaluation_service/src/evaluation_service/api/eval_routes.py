"""Verification and evaluation REST API endpoints."""

from typing import Annotated

from atlas_contracts.evaluation import (
    CitationVerificationRequest,
    CitationVerificationResult,
    ClaimVerificationRecord,
    ClaimVerificationRequest,
)
from evaluation_service.auditor.citation_auditor import CitationAuditor
from evaluation_service.verifier.engine import EvidenceVerificationEngine
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/api/v1/evaluation", tags=["Evaluation"])

_auditor_instance: CitationAuditor | None = None
_engine_instance: EvidenceVerificationEngine | None = None


def get_verification_engine() -> EvidenceVerificationEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = EvidenceVerificationEngine()
    return _engine_instance


def get_citation_auditor() -> CitationAuditor:
    global _auditor_instance
    if _auditor_instance is None:
        _auditor_instance = CitationAuditor()
    return _auditor_instance


@router.post(
    "/verify-claims",
    response_model=list[ClaimVerificationRecord],
    status_code=status.HTTP_200_OK,
    summary="Verify batch of claims against reference passages",
)
async def verify_claims_endpoint(
    payload: ClaimVerificationRequest,
    engine: Annotated[EvidenceVerificationEngine, Depends(get_verification_engine)],
) -> list[ClaimVerificationRecord]:
    return [engine.verify_claim(claim, payload.passages) for claim in payload.claims]


@router.post(
    "/audit-report",
    response_model=CitationVerificationResult,
    status_code=status.HTTP_200_OK,
    summary="Audit report citation precision, faithfulness, and support status",
)
async def audit_report_endpoint(
    payload: CitationVerificationRequest,
    auditor: Annotated[CitationAuditor, Depends(get_citation_auditor)],
) -> CitationVerificationResult:
    return auditor.audit_report(payload)
