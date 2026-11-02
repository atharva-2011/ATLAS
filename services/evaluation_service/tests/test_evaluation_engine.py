"""Comprehensive unit and integration tests for Phase 9 Evidence Verification and Citation Auditor."""

from atlas_contracts.evaluation import (
    CitationVerificationRequest,
    ClaimSupportStatus,
    NormalizedClaim,
)
from evaluation_service.auditor.citation_auditor import CitationAuditor
from evaluation_service.claims.normalizer import ClaimNormalizer, extract_inline_citations
from evaluation_service.core.config import Settings
from evaluation_service.main import create_app
from evaluation_service.verifier.engine import EvidenceVerificationEngine
from fastapi.testclient import TestClient

# ============================================================================
# 1. Claim Normalizer & Inline Citation Extraction
# ============================================================================


def test_extract_inline_citations():
    text = "Battery cycle life increases with silicon content [ev_bat_01] while p95 latency remains low [chunk_99]."
    cites = extract_inline_citations(text)
    assert "ev_bat_01" in cites
    assert "chunk_99" in cites
    assert len(cites) == 2


def test_claim_normalizer_distinguishes_opinion_and_fact():
    normalizer = ClaimNormalizer()

    factual = "The system achieved 99.9% uptime over a 180 day observation window [ev_up_1]."
    norm_fact = normalizer.normalize_sentence(factual)
    assert not norm_fact.is_opinion_or_analysis
    assert "ev_up_1" in norm_fact.cited_evidence_ids
    assert "The system achieved 99.9% uptime" in norm_fact.text

    opinion = "We believe this architecture might scale more efficiently in future iterations."
    norm_op = normalizer.normalize_sentence(opinion)
    assert norm_op.is_opinion_or_analysis


# ============================================================================
# 2. Evidence Verification Engine Tests
# ============================================================================


def test_verify_claim_supported():
    engine = EvidenceVerificationEngine()
    claim = NormalizedClaim(
        text="Empirical testing confirmed sub-50ms latency at p95.",
        cited_evidence_ids=["ev_1"],
    )
    passages = [
        {
            "evidence_id": "ev_1",
            "passage": "Empirical testing confirmed sub-50ms latency at p95 under standard workload conditions.",
            "locator": {"page": 3},
        }
    ]

    record = engine.verify_claim(claim, passages)
    assert record.status == ClaimSupportStatus.SUPPORTED
    assert record.confidence > 0.8
    assert "ev_1" in record.supporting_evidence_ids
    assert record.provenance_locator.get("page") == 3


def test_verify_claim_contradicted():
    engine = EvidenceVerificationEngine()
    claim = NormalizedClaim(
        text="Experimental results showed higher throughput.",
        cited_evidence_ids=["ev_2"],
    )
    passages = [
        {
            "evidence_id": "ev_2",
            "passage": "Experimental results showed lower throughput across all parallel nodes.",
        }
    ]

    record = engine.verify_claim(claim, passages)
    assert record.status == ClaimSupportStatus.CONTRADICTED
    assert record.contradiction_text is not None


def test_verify_claim_unsupported():
    engine = EvidenceVerificationEngine()
    claim = NormalizedClaim(
        text="The rocket booster landed on Mars successfully.",
    )
    passages = [
        {
            "evidence_id": "ev_tech",
            "passage": "PostgreSQL database configuration handles high transaction volume.",
        }
    ]

    record = engine.verify_claim(claim, passages)
    assert record.status == ClaimSupportStatus.UNSUPPORTED


# ============================================================================
# 3. Citation Auditor and Report Audit Tests
# ============================================================================


def test_citation_auditor_report():
    auditor = CitationAuditor()
    report = """# Executive Research Report

Empirical testing confirmed sub-50ms latency at p95 [ev_perf_1].
The server cluster maintained 99.9% uptime throughout the quarter [ev_uptime_2].
We believe this design could perhaps support further horizontal scale.
Invented metric without source reference was observed [ev_ghost_99].
"""
    evidence = [
        {
            "evidence_id": "ev_perf_1",
            "passage": "Empirical testing confirmed sub-50ms latency at p95 under standard load.",
        },
        {
            "evidence_id": "ev_uptime_2",
            "passage": "The server cluster maintained 99.9% uptime throughout the quarter.",
        },
    ]

    req = CitationVerificationRequest(
        report_title="Performance Report",
        report_markdown=report,
        referenced_evidence=evidence,
    )
    res = auditor.audit_report(req)

    assert res.total_citations == 3
    assert res.resolved_citations == 2
    assert "ev_ghost_99" in res.unresolved_citations
    assert 0.6 <= res.citation_precision <= 0.7
    assert res.supported_claims_count >= 2


# ============================================================================
# 4. Evaluation REST API Route Tests
# ============================================================================


def test_api_verify_claims():
    settings = Settings()
    app = create_app(settings=settings)
    client = TestClient(app)

    payload = {
        "claims": [
            {
                "text": "PostgreSQL provides transactional consistency.",
                "cited_evidence_ids": ["ev_pg"],
            }
        ],
        "passages": [
            {
                "evidence_id": "ev_pg",
                "passage": "PostgreSQL provides transactional consistency and ACID compliance.",
            }
        ],
    }
    response = client.post("/api/v1/evaluation/verify-claims", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "supported"


def test_api_audit_report():
    settings = Settings()
    app = create_app(settings=settings)
    client = TestClient(app)

    payload = {
        "report_title": "Architecture Report",
        "report_markdown": "High availability was verified at 99.9% uptime [ev_ha_1].",
        "referenced_evidence": [
            {
                "evidence_id": "ev_ha_1",
                "passage": "High availability was verified at 99.9% uptime in production.",
            }
        ],
    }
    response = client.post("/api/v1/evaluation/audit-report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_citations"] == 1
    assert data["resolved_citations"] == 1
    assert data["faithfulness_score"] >= 0.9
