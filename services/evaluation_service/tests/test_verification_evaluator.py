"""Unit tests for the Claim Grounding and Verification Evaluator."""

import json
from pathlib import Path

import pytest
from evaluation_service.metrics.verification_evaluator import VerificationEvaluator

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "gold_sets"


@pytest.fixture
def evaluator() -> VerificationEvaluator:
    return VerificationEvaluator()


def test_evaluate_claim_cases_with_gold_set(evaluator: VerificationEvaluator) -> None:
    gold_path = FIXTURES_DIR / "claim_verification_gold_set.json"
    with open(gold_path, encoding="utf-8") as f:
        data = json.load(f)

    cases = data["test_cases"]
    summary, details = evaluator.evaluate_claim_cases(cases)

    assert summary.total_cases == len(cases)
    assert summary.accuracy >= 0.80
    assert summary.macro_f1 >= 0.80
    assert summary.hallucination_detection_recall == 1.0
    assert summary.contradiction_detection_recall == 1.0
    assert len(details) == len(cases)

    # Check that each detail has expected fields
    for d in details:
        assert "case_id" in d
        assert "expected" in d
        assert "predicted" in d
        assert "is_correct" in d


def test_audit_golden_report(evaluator: VerificationEvaluator) -> None:
    scenario_path = FIXTURES_DIR / "research_scenarios.json"
    with open(scenario_path, encoding="utf-8") as f:
        data = json.load(f)

    scenario = data["scenarios"][0]
    audit_res = evaluator.audit_report_markdown(
        report_title=scenario["topic"],
        report_markdown=scenario["golden_report_markdown"],
        referenced_evidence=scenario["referenced_evidence"],
    )

    assert audit_res.total_citations == 2
    assert audit_res.resolved_citations == 2
    assert len(audit_res.unresolved_citations) == 0
    assert audit_res.citation_precision == 1.0
    assert audit_res.faithfulness_score >= 0.80
    assert audit_res.contradicted_claims_count == 0


def test_audit_corrupted_report(evaluator: VerificationEvaluator) -> None:
    scenario_path = FIXTURES_DIR / "research_scenarios.json"
    with open(scenario_path, encoding="utf-8") as f:
        data = json.load(f)

    scenario = data["scenarios"][0]
    audit_res = evaluator.audit_report_markdown(
        report_title=scenario["topic"],
        report_markdown=scenario["corrupted_report_markdown"],
        referenced_evidence=scenario["referenced_evidence"],
    )

    # Must detect the unreferenced citation "chunk_unknown_999"
    assert "chunk_unknown_999" in audit_res.unresolved_citations
    assert audit_res.citation_precision < 1.0

    # Must detect either contradicted or unsupported claim
    assert (audit_res.contradicted_claims_count > 0) or (audit_res.unsupported_claims_count > 0)
    assert audit_res.faithfulness_score < 1.0
