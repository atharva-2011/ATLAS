"""Retrieval and Ranking Metrics Evaluator for ATLAS.

Calculates Recall@k, Precision@k, Mean Reciprocal Rank (MRR),
Normalized Discounted Cumulative Gain (nDCG@k), and relative model/reranker lift.
"""

import math

from atlas_contracts.evaluation import (
    RetrievalBenchmarkScorecard,
    RetrievalQueryEvaluation,
)


class RetrievalEvaluator:
    """Computes standard information retrieval metrics and benchmark scorecards."""

    DEFAULT_K_VALUES: list[int] = [1, 3, 5, 10]

    @staticmethod
    def calculate_recall_at_k(
        retrieved: list[str],
        relevant: set[str],
        k: int,
    ) -> float:
        """Recall@k = |retrieved_1..k ∩ relevant| / |relevant|."""
        if not relevant or k <= 0:
            return 0.0
        hits = len(set(retrieved[:k]).intersection(relevant))
        return round(hits / len(relevant), 4)

    @staticmethod
    def calculate_precision_at_k(
        retrieved: list[str],
        relevant: set[str],
        k: int,
    ) -> float:
        """Precision@k = |retrieved_1..k ∩ relevant| / k."""
        if k <= 0:
            return 0.0
        hits = len(set(retrieved[:k]).intersection(relevant))
        return round(hits / k, 4)

    @staticmethod
    def calculate_reciprocal_rank(
        retrieved: list[str],
        relevant: set[str],
    ) -> float:
        """Reciprocal Rank (RR) = 1 / first_relevant_rank."""
        for idx, chunk_id in enumerate(retrieved, start=1):
            if chunk_id in relevant:
                return round(1.0 / idx, 4)
        return 0.0

    @staticmethod
    def calculate_ndcg_at_k(
        retrieved: list[str],
        graded_relevance: dict[str, float],
        k: int,
    ) -> float:
        """Normalized Discounted Cumulative Gain at rank k."""
        if not graded_relevance or k <= 0:
            return 0.0

        dcg = 0.0
        for idx, chunk_id in enumerate(retrieved[:k], start=1):
            rel = graded_relevance.get(chunk_id, 0.0)
            if rel > 0:
                dcg += (math.pow(2.0, rel) - 1.0) / math.log2(idx + 1)

        sorted_rels = sorted(graded_relevance.values(), reverse=True)
        idcg = 0.0
        for idx, rel in enumerate(sorted_rels[:k], start=1):
            if rel > 0:
                idcg += (math.pow(2.0, rel) - 1.0) / math.log2(idx + 1)

        if idcg <= 0.0:
            return 0.0
        return round(dcg / idcg, 4)

    def evaluate_query(
        self,
        query_id: str,
        query: str,
        retrieved_chunk_ids: list[str],
        relevant_chunk_ids: list[str],
        graded_relevance: dict[str, float] | None = None,
        k_list: list[int] | None = None,
    ) -> RetrievalQueryEvaluation:
        """Evaluates a single query's retrieved ranked candidates against ground truth."""
        ks = k_list or self.DEFAULT_K_VALUES
        rel_set = set(relevant_chunk_ids)
        graded = graded_relevance or dict.fromkeys(relevant_chunk_ids, 1.0)

        recall_dict: dict[int, float] = {}
        precision_dict: dict[int, float] = {}
        ndcg_dict: dict[int, float] = {}

        for k in ks:
            recall_dict[k] = self.calculate_recall_at_k(retrieved_chunk_ids, rel_set, k)
            precision_dict[k] = self.calculate_precision_at_k(retrieved_chunk_ids, rel_set, k)
            ndcg_dict[k] = self.calculate_ndcg_at_k(retrieved_chunk_ids, graded, k)

        rr = self.calculate_reciprocal_rank(retrieved_chunk_ids, rel_set)

        return RetrievalQueryEvaluation(
            query_id=query_id,
            query=query,
            retrieved_chunk_ids=retrieved_chunk_ids,
            relevant_chunk_ids=relevant_chunk_ids,
            recall_at_k=recall_dict,
            reciprocal_rank=rr,
            ndcg_at_k=ndcg_dict,
            precision_at_k=precision_dict,
        )

    def evaluate_dataset(
        self,
        query_evaluations: list[RetrievalQueryEvaluation],
        benchmark_name: str = "ATLAS Retrieval Benchmark",
        k_list: list[int] | None = None,
    ) -> RetrievalBenchmarkScorecard:
        """Aggregates per-query evaluations into a macro-averaged scorecard."""
        ks = k_list or self.DEFAULT_K_VALUES
        total = len(query_evaluations)
        if total == 0:
            return RetrievalBenchmarkScorecard(
                benchmark_name=benchmark_name,
                total_queries=0,
                mrr=0.0,
            )

        mean_recalls: dict[int, float] = {
            k: round(sum(q.recall_at_k.get(k, 0.0) for q in query_evaluations) / total, 4)
            for k in ks
        }
        mean_precisions: dict[int, float] = {
            k: round(sum(q.precision_at_k.get(k, 0.0) for q in query_evaluations) / total, 4)
            for k in ks
        }
        mean_ndcgs: dict[int, float] = {
            k: round(sum(q.ndcg_at_k.get(k, 0.0) for q in query_evaluations) / total, 4)
            for k in ks
        }
        mean_rr = round(sum(q.reciprocal_rank for q in query_evaluations) / total, 4)

        return RetrievalBenchmarkScorecard(
            benchmark_name=benchmark_name,
            total_queries=total,
            mean_recall_at_k=mean_recalls,
            mrr=mean_rr,
            mean_ndcg_at_k=mean_ndcgs,
            mean_precision_at_k=mean_precisions,
            per_query_results=query_evaluations,
        )

    @staticmethod
    def calculate_lift(
        candidate: RetrievalBenchmarkScorecard,
        baseline: RetrievalBenchmarkScorecard,
    ) -> dict[str, float]:
        """Calculates relative performance lift (%) between candidate and baseline scorecards."""
        lift: dict[str, float] = {}

        # MRR lift
        base_mrr = baseline.mrr
        cand_mrr = candidate.mrr
        lift["mrr_delta"] = round(cand_mrr - base_mrr, 4)
        lift["mrr_relative_pct"] = (
            round(((cand_mrr - base_mrr) / base_mrr) * 100.0, 2) if base_mrr > 0 else 0.0
        )

        # Recall@k lifts
        for k, cand_rec in candidate.mean_recall_at_k.items():
            base_rec = baseline.mean_recall_at_k.get(k, 0.0)
            lift[f"recall@{k}_delta"] = round(cand_rec - base_rec, 4)
            lift[f"recall@{k}_relative_pct"] = (
                round(((cand_rec - base_rec) / base_rec) * 100.0, 2) if base_rec > 0 else 0.0
            )

        # nDCG@k lifts
        for k, cand_ndcg in candidate.mean_ndcg_at_k.items():
            base_ndcg = baseline.mean_ndcg_at_k.get(k, 0.0)
            lift[f"ndcg@{k}_delta"] = round(cand_ndcg - base_ndcg, 4)
            lift[f"ndcg@{k}_relative_pct"] = (
                round(((cand_ndcg - base_ndcg) / base_ndcg) * 100.0, 2) if base_ndcg > 0 else 0.0
            )

        return lift
