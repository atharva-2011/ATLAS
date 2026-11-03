"""Integration test for Phase 12 Quality Gate Benchmarks and Regression Detection."""

from pathlib import Path

from evaluation_service.metrics.retrieval_evaluator import RetrievalEvaluator
from evaluation_service.metrics.verification_evaluator import VerificationEvaluator

from infrastructure.scripts.run_quality_benchmarks import (
    DEFAULT_THRESHOLDS,
    evaluate_quality_gates,
    run_report_benchmark,
    run_retrieval_benchmark,
    run_verification_benchmark,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "gold_sets"


def test_quality_benchmarks_integration_all_gates_pass() -> None:
    retrieval_eval = RetrievalEvaluator()
    verification_eval = VerificationEvaluator()

    retrieval_res, ret_ok = run_retrieval_benchmark(FIXTURES_DIR, retrieval_eval)
    assert ret_ok is True
    assert retrieval_res["total_queries"] >= 5
    assert retrieval_res["mrr"] >= DEFAULT_THRESHOLDS["retrieval_mrr"]

    verification_res, ver_ok = run_verification_benchmark(FIXTURES_DIR, verification_eval)
    assert ver_ok is True
    assert verification_res["case_count"] >= 4
    assert (
        verification_res["summary"]["accuracy"]
        >= DEFAULT_THRESHOLDS["claim_verification_accuracy"]
    )

    report_res, rep_ok = run_report_benchmark(FIXTURES_DIR, verification_eval)
    assert rep_ok is True
    assert len(report_res["scenarios"]) >= 1

    gates, all_passed = evaluate_quality_gates(
        retrieval_res=retrieval_res,
        verification_res=verification_res,
        report_res=report_res,
        thresholds=DEFAULT_THRESHOLDS,
    )

    assert all_passed is True
    assert len(gates) >= 9
    for g in gates:
        assert g["status"] == "PASS", f"Gate {g['gate']} failed: measured {g['measured']} vs target {g['target']}"


def test_quality_benchmarks_regression_detection() -> None:
    """Verifies that if thresholds are unmet, all_passed evaluates to False."""
    retrieval_eval = RetrievalEvaluator()
    verification_eval = VerificationEvaluator()

    retrieval_res, _ = run_retrieval_benchmark(FIXTURES_DIR, retrieval_eval)
    verification_res, _ = run_verification_benchmark(FIXTURES_DIR, verification_eval)
    report_res, _ = run_report_benchmark(FIXTURES_DIR, verification_eval)

    # Artificially strict threshold to simulate gate tripping
    strict_thresholds = dict(DEFAULT_THRESHOLDS)
    strict_thresholds["retrieval_mrr"] = 1.01  # Impossible target

    gates, all_passed = evaluate_quality_gates(
        retrieval_res=retrieval_res,
        verification_res=verification_res,
        report_res=report_res,
        thresholds=strict_thresholds,
    )

    assert all_passed is False
    mrr_gate = next(g for g in gates if g["gate"] == "MRR")
    assert mrr_gate["status"] == "FAIL"
