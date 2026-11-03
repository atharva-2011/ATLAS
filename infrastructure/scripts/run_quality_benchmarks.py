"""ATLAS Release Quality Gate and Benchmark Runner.

Executes standardized evaluation benchmarks against gold standard datasets:
1. Information Retrieval (BM25 & Hybrid Ranking): Recall@k, MRR, nDCG@k
2. Claim Grounding & Verification: Accuracy, Macro F1, Hallucination Recall, Contradiction Recall
3. Report Synthesis & Citation Fidelity: Faithfulness Score, Citation Precision, Anomaly Detection

Enforces production quality gates before release.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# Ensure root directory is on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Add services and shared to path for isolated execution
for p in [
    ROOT_DIR / "shared" / "contracts" / "src",
    ROOT_DIR / "shared" / "observability" / "src",
    ROOT_DIR / "services" / "evaluation_service" / "src",
    ROOT_DIR / "services" / "retrieval_service" / "src",
]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from evaluation_service.metrics.retrieval_evaluator import RetrievalEvaluator  # noqa: E402
from evaluation_service.metrics.verification_evaluator import VerificationEvaluator  # noqa: E402
from retrieval_service.sparse.bm25_store import BM25Store  # noqa: E402

# Default Release Quality Gate Thresholds
DEFAULT_THRESHOLDS = {
    "retrieval_recall_at_5": 0.70,
    "retrieval_mrr": 0.60,
    "retrieval_ndcg_at_5": 0.60,
    "claim_verification_accuracy": 0.80,
    "claim_verification_macro_f1": 0.75,
    "hallucination_detection_recall": 0.90,
    "contradiction_detection_recall": 0.90,
    "report_citation_precision": 0.95,
    "report_faithfulness_score": 0.85,
}


def run_retrieval_benchmark(
    fixtures_dir: Path,
    evaluator: RetrievalEvaluator,
) -> tuple[dict, bool]:
    """Runs retrieval queries over gold corpus using BM25 store and calculates ranking metrics."""
    gold_path = fixtures_dir / "retrieval_gold_set.json"
    with open(gold_path, encoding="utf-8") as f:
        data = json.load(f)

    corpus = data["corpus"]
    queries = data["queries"]

    # Initialize BM25 store and index gold chunks
    bm25_store = BM25Store()
    tenant_id = "gold_eval_tenant"
    doc_id = uuid4()

    bm25_store.index_chunks(
        tenant_id=tenant_id,
        document_id=doc_id,
        chunks=corpus,
    )

    query_evaluations = []
    for q in queries:
        qid = q["query_id"]
        qtext = q["query"]
        relevant_ids = q["relevant_chunk_ids"]
        graded = q.get("graded_relevance")

        search_results = bm25_store.search(
            tenant_id=tenant_id,
            query=qtext,
            top_k=10,
        )
        retrieved_ids = [str(r["chunk_id"]) for r in search_results]

        ev = evaluator.evaluate_query(
            query_id=qid,
            query=qtext,
            retrieved_chunk_ids=retrieved_ids,
            relevant_chunk_ids=relevant_ids,
            graded_relevance=graded,
            k_list=[1, 3, 5, 10],
        )
        query_evaluations.append(ev)

    scorecard = evaluator.evaluate_dataset(
        query_evaluations=query_evaluations,
        benchmark_name="ATLAS Gold Retrieval Benchmark",
        k_list=[1, 3, 5, 10],
    )

    return scorecard.model_dump(), True


def run_verification_benchmark(
    fixtures_dir: Path,
    evaluator: VerificationEvaluator,
) -> tuple[dict, bool]:
    """Runs claim verification over gold standard cases."""
    gold_path = fixtures_dir / "claim_verification_gold_set.json"
    with open(gold_path, encoding="utf-8") as f:
        data = json.load(f)

    summary, details = evaluator.evaluate_claim_cases(data["test_cases"])
    return {
        "summary": summary.model_dump(),
        "case_count": len(details),
    }, True


def run_report_benchmark(
    fixtures_dir: Path,
    evaluator: VerificationEvaluator,
) -> tuple[dict, bool]:
    """Runs report citation and faithfulness audits on golden and corrupted scenario reports."""
    scenario_path = fixtures_dir / "research_scenarios.json"
    with open(scenario_path, encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data["scenarios"]
    scenario_results = []

    for sc in scenarios:
        # Golden report audit
        golden_audit = evaluator.audit_report_markdown(
            report_title=sc["topic"],
            report_markdown=sc["golden_report_markdown"],
            referenced_evidence=sc["referenced_evidence"],
        )

        # Corrupted report audit
        corrupted_audit = evaluator.audit_report_markdown(
            report_title=sc["topic"],
            report_markdown=sc["corrupted_report_markdown"],
            referenced_evidence=sc["referenced_evidence"],
        )

        scenario_results.append(
            {
                "scenario_id": sc["scenario_id"],
                "golden": golden_audit.model_dump(),
                "corrupted": corrupted_audit.model_dump(),
            }
        )

    return {"scenarios": scenario_results}, True


def evaluate_quality_gates(
    retrieval_res: dict,
    verification_res: dict,
    report_res: dict,
    thresholds: dict[str, float],
) -> tuple[list[dict], bool]:
    """Checks measured benchmark results against predefined release quality thresholds."""
    gates = []
    all_passed = True

    # 1. Retrieval Gates
    m_rec_dict = retrieval_res.get("mean_recall_at_k", {})
    m_rec5 = m_rec_dict.get(5, m_rec_dict.get("5", 0.0))
    t_rec5 = thresholds["retrieval_recall_at_5"]
    p_rec5 = m_rec5 >= t_rec5
    gates.append({
        "category": "Retrieval",
        "gate": "Recall@5",
        "measured": m_rec5,
        "target": t_rec5,
        "status": "PASS" if p_rec5 else "FAIL",
    })
    if not p_rec5:
        all_passed = False

    m_mrr = retrieval_res.get("mrr", 0.0)
    t_mrr = thresholds["retrieval_mrr"]
    p_mrr = m_mrr >= t_mrr
    gates.append({
        "category": "Retrieval",
        "gate": "MRR",
        "measured": m_mrr,
        "target": t_mrr,
        "status": "PASS" if p_mrr else "FAIL",
    })
    if not p_mrr:
        all_passed = False

    m_ndcg_dict = retrieval_res.get("mean_ndcg_at_k", {})
    m_ndcg5 = m_ndcg_dict.get(5, m_ndcg_dict.get("5", 0.0))
    t_ndcg5 = thresholds["retrieval_ndcg_at_5"]
    p_ndcg5 = m_ndcg5 >= t_ndcg5
    gates.append({
        "category": "Retrieval",
        "gate": "nDCG@5",
        "measured": m_ndcg5,
        "target": t_ndcg5,
        "status": "PASS" if p_ndcg5 else "FAIL",
    })
    if not p_ndcg5:
        all_passed = False

    # 2. Claim Verification Gates
    v_summary = verification_res.get("summary", {})
    m_acc = v_summary.get("accuracy", 0.0)
    t_acc = thresholds["claim_verification_accuracy"]
    p_acc = m_acc >= t_acc
    gates.append({
        "category": "Claim Verification",
        "gate": "Accuracy",
        "measured": m_acc,
        "target": t_acc,
        "status": "PASS" if p_acc else "FAIL",
    })
    if not p_acc:
        all_passed = False

    m_f1 = v_summary.get("macro_f1", 0.0)
    t_f1 = thresholds["claim_verification_macro_f1"]
    p_f1 = m_f1 >= t_f1
    gates.append({
        "category": "Claim Verification",
        "gate": "Macro F1",
        "measured": m_f1,
        "target": t_f1,
        "status": "PASS" if p_f1 else "FAIL",
    })
    if not p_f1:
        all_passed = False

    m_hall = v_summary.get("hallucination_detection_recall", 0.0)
    t_hall = thresholds["hallucination_detection_recall"]
    p_hall = m_hall >= t_hall
    gates.append({
        "category": "Claim Verification",
        "gate": "Hallucination Recall",
        "measured": m_hall,
        "target": t_hall,
        "status": "PASS" if p_hall else "FAIL",
    })
    if not p_hall:
        all_passed = False

    m_cont = v_summary.get("contradiction_detection_recall", 0.0)
    t_cont = thresholds["contradiction_detection_recall"]
    p_cont = m_cont >= t_cont
    gates.append({
        "category": "Claim Verification",
        "gate": "Contradiction Recall",
        "measured": m_cont,
        "target": t_cont,
        "status": "PASS" if p_cont else "FAIL",
    })
    if not p_cont:
        all_passed = False

    # 3. Report Synthesis Gates
    first_sc = (
        report_res.get("scenarios", [{}])[0] if report_res.get("scenarios") else {}
    )
    golden_data = first_sc.get("golden", {})
    m_c_prec = golden_data.get("citation_precision", 0.0)
    t_c_prec = thresholds["report_citation_precision"]
    p_c_prec = m_c_prec >= t_c_prec
    gates.append({
        "category": "Report Synthesis",
        "gate": "Citation Precision",
        "measured": m_c_prec,
        "target": t_c_prec,
        "status": "PASS" if p_c_prec else "FAIL",
    })
    if not p_c_prec:
        all_passed = False

    m_faith = golden_data.get("faithfulness_score", 0.0)
    t_faith = thresholds["report_faithfulness_score"]
    p_faith = m_faith >= t_faith
    gates.append({
        "category": "Report Synthesis",
        "gate": "Faithfulness Score",
        "measured": m_faith,
        "target": t_faith,
        "status": "PASS" if p_faith else "FAIL",
    })
    if not p_faith:
        all_passed = False

    # Corrupted Report Anomaly Detection
    corrupted_data = first_sc.get("corrupted", {})
    corrupted_detected = (
        len(corrupted_data.get("unresolved_citations", [])) > 0
        and corrupted_data.get("citation_precision", 1.0) < 1.0
    )
    gates.append({
        "category": "Report Synthesis",
        "gate": "Anomaly / Hallucination Detection",
        "measured": 1.0 if corrupted_detected else 0.0,
        "target": 1.0,
        "status": "PASS" if corrupted_detected else "FAIL",
    })
    if not corrupted_detected:
        all_passed = False

    return gates, all_passed


def print_scorecard(gates: list[dict], all_passed: bool) -> None:
    """Prints a structured ASCII quality scorecard table."""
    border = "=" * 78
    sep = "-" * 78
    print("\n" + border)
    print("                    ATLAS PRODUCTION QUALITY SCORECARD")
    print(border)
    print(f"{'Category':<20} | {'Gate / Metric':<26} | {'Target':<8} | {'Measured':<8} | {'Status'}")
    print(sep)

    for g in gates:
        plain_status = f"[{g['status']}]"
        print(
            f"{g['category']:<20} | {g['gate']:<26} | {g['target']:<8.2f} | {g['measured']:<8.2f} | {plain_status}"
        )

    print(border)
    if all_passed:
        print(" OVERALL RELEASE GATE VERDICT: PASSED (All Quality Standards Satisfied)")
    else:
        print(" OVERALL RELEASE GATE VERDICT: FAILED (Quality Regression Detected)")
    print(border + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ATLAS release quality benchmarks.")
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=ROOT_DIR / "tests" / "fixtures" / "gold_sets",
        help="Path to gold standard fixtures directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT_DIR / "benchmark_scorecard.json",
        help="Path to export benchmark scorecard JSON",
    )
    args = parser.parse_args()

    fixtures_dir: Path = args.fixtures_dir
    if not fixtures_dir.exists():
        print(f"Error: Fixtures directory not found at {fixtures_dir}", file=sys.stderr)
        sys.exit(1)

    retrieval_eval = RetrievalEvaluator()
    verification_eval = VerificationEvaluator()

    # 1. Retrieval Benchmark
    retrieval_results, _ = run_retrieval_benchmark(fixtures_dir, retrieval_eval)

    # 2. Claim Verification Benchmark
    verification_results, _ = run_verification_benchmark(fixtures_dir, verification_eval)

    # 3. Report Synthesis Benchmark
    report_results, _ = run_report_benchmark(fixtures_dir, verification_eval)

    # 4. Evaluate Quality Gates
    gates, all_passed = evaluate_quality_gates(
        retrieval_res=retrieval_results,
        verification_res=verification_results,
        report_res=report_results,
        thresholds=DEFAULT_THRESHOLDS,
    )

    # 5. Display Scorecard
    print_scorecard(gates, all_passed)

    # 6. Save JSON artifact
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "overall_status": "PASS" if all_passed else "FAIL",
        "gates": gates,
        "retrieval_benchmark": retrieval_results,
        "verification_benchmark": verification_results,
        "report_benchmark": report_results,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Artifact exported to: {args.output}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
