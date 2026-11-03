"""Unit tests for the Retrieval and Ranking Metrics Evaluator."""

import pytest
from evaluation_service.metrics.retrieval_evaluator import RetrievalEvaluator


@pytest.fixture
def evaluator() -> RetrievalEvaluator:
    return RetrievalEvaluator()


def test_calculate_recall_at_k(evaluator: RetrievalEvaluator) -> None:
    relevant = {"chunk_1", "chunk_2"}
    retrieved = ["chunk_1", "chunk_3", "chunk_2", "chunk_4"]

    assert evaluator.calculate_recall_at_k(retrieved, relevant, k=1) == 0.5
    assert evaluator.calculate_recall_at_k(retrieved, relevant, k=2) == 0.5
    assert evaluator.calculate_recall_at_k(retrieved, relevant, k=3) == 1.0
    assert evaluator.calculate_recall_at_k(retrieved, relevant, k=10) == 1.0
    assert evaluator.calculate_recall_at_k([], relevant, k=5) == 0.0
    assert evaluator.calculate_recall_at_k(retrieved, set(), k=5) == 0.0


def test_calculate_precision_at_k(evaluator: RetrievalEvaluator) -> None:
    relevant = {"chunk_1", "chunk_2"}
    retrieved = ["chunk_1", "chunk_3", "chunk_2", "chunk_4"]

    assert evaluator.calculate_precision_at_k(retrieved, relevant, k=1) == 1.0
    assert evaluator.calculate_precision_at_k(retrieved, relevant, k=2) == 0.5
    assert evaluator.calculate_precision_at_k(retrieved, relevant, k=4) == 0.5
    assert evaluator.calculate_precision_at_k(retrieved, relevant, k=0) == 0.0


def test_calculate_reciprocal_rank(evaluator: RetrievalEvaluator) -> None:
    relevant = {"target_doc"}

    # Rank 1 -> RR = 1.0
    assert evaluator.calculate_reciprocal_rank(["target_doc", "doc_b"], relevant) == 1.0
    # Rank 2 -> RR = 0.5
    assert evaluator.calculate_reciprocal_rank(["doc_a", "target_doc"], relevant) == 0.5
    # Rank 4 -> RR = 0.25
    assert (
        evaluator.calculate_reciprocal_rank(["doc_a", "doc_b", "doc_c", "target_doc"], relevant)
        == 0.25
    )
    # Not found -> RR = 0.0
    assert evaluator.calculate_reciprocal_rank(["doc_a", "doc_b"], relevant) == 0.0


def test_calculate_ndcg_at_k(evaluator: RetrievalEvaluator) -> None:
    graded = {"doc_1": 3.0, "doc_2": 2.0, "doc_3": 1.0}

    # Ideal order: doc_1, doc_2, doc_3 -> nDCG@3 = 1.0
    assert evaluator.calculate_ndcg_at_k(["doc_1", "doc_2", "doc_3"], graded, k=3) == 1.0

    # Sub-optimal order: doc_3, doc_2, doc_1
    suboptimal = evaluator.calculate_ndcg_at_k(["doc_3", "doc_2", "doc_1"], graded, k=3)
    assert 0.0 < suboptimal < 1.0

    # No relevance
    assert evaluator.calculate_ndcg_at_k(["doc_x", "doc_y"], graded, k=2) == 0.0
    assert evaluator.calculate_ndcg_at_k(["doc_1"], {}, k=1) == 0.0


def test_evaluate_query(evaluator: RetrievalEvaluator) -> None:
    res = evaluator.evaluate_query(
        query_id="q1",
        query="What is diabetic retinopathy?",
        retrieved_chunk_ids=["chunk_med_01", "chunk_med_02"],
        relevant_chunk_ids=["chunk_med_01"],
        graded_relevance={"chunk_med_01": 3.0},
        k_list=[1, 3, 5],
    )

    assert res.query_id == "q1"
    assert res.reciprocal_rank == 1.0
    assert res.recall_at_k[1] == 1.0
    assert res.precision_at_k[1] == 1.0
    assert res.ndcg_at_k[1] == 1.0


def test_evaluate_dataset_and_lift(evaluator: RetrievalEvaluator) -> None:
    q1 = evaluator.evaluate_query(
        query_id="q1",
        query="query 1",
        retrieved_chunk_ids=["c1", "c2"],
        relevant_chunk_ids=["c1"],
        k_list=[1, 5],
    )
    q2 = evaluator.evaluate_query(
        query_id="q2",
        query="query 2",
        retrieved_chunk_ids=["c9", "c2"],
        relevant_chunk_ids=["c2"],
        k_list=[1, 5],
    )

    scorecard = evaluator.evaluate_dataset([q1, q2], benchmark_name="Test Benchmark", k_list=[1, 5])
    assert scorecard.total_queries == 2
    # q1 RR=1.0, q2 RR=0.5 -> MRR = 0.75
    assert scorecard.mrr == 0.75
    # q1 recall@1=1.0, q2 recall@1=0.0 -> mean recall@1 = 0.5
    assert scorecard.mean_recall_at_k[1] == 0.5
    # both recall@5=1.0 -> mean recall@5 = 1.0
    assert scorecard.mean_recall_at_k[5] == 1.0

    # Test baseline vs candidate lift
    baseline_q2 = evaluator.evaluate_query(
        query_id="q2",
        query="query 2",
        retrieved_chunk_ids=["c9", "c8", "c2"],
        relevant_chunk_ids=["c2"],
        k_list=[1, 5],
    )
    baseline_scorecard = evaluator.evaluate_dataset(
        [q1, baseline_q2], benchmark_name="Baseline", k_list=[1, 5]
    )

    lift = evaluator.calculate_lift(scorecard, baseline_scorecard)
    assert "mrr_delta" in lift
    assert lift["mrr_delta"] > 0
    assert lift["mrr_relative_pct"] > 0
