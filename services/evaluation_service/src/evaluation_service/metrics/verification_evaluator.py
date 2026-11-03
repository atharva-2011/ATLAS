"""Claim Grounding, Contradiction Detection, and Faithfulness Evaluator.

Calculates multi-class classification metrics (Precision, Recall, F1)
for claim verification, citation resolution precision, and hallucination detection.
"""

from typing import Any

from atlas_contracts.evaluation import (
    CitationVerificationRequest,
    CitationVerificationResult,
    ClaimSupportStatus,
    ClaimVerificationRecord,
    NormalizedClaim,
)
from pydantic import BaseModel, Field

from evaluation_service.auditor.citation_auditor import CitationAuditor
from evaluation_service.verifier.engine import EvidenceVerificationEngine


class ClaimEvaluationMetricSummary(BaseModel):
    """Aggregated evaluation metrics for claim verification over gold standard cases."""

    total_cases: int
    correct_predictions: int
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    macro_f1: float = Field(default=0.0, ge=0.0, le=1.0)
    hallucination_detection_recall: float = Field(default=0.0, ge=0.0, le=1.0)
    contradiction_detection_recall: float = Field(default=0.0, ge=0.0, le=1.0)
    per_status_metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    confusion_matrix: dict[str, int] = Field(default_factory=dict)


class VerificationEvaluator:
    """Evaluates factual grounding engines and report synthesis against ground truth."""

    def __init__(
        self,
        verification_engine: EvidenceVerificationEngine | None = None,
        citation_auditor: CitationAuditor | None = None,
    ) -> None:
        self.engine = verification_engine or EvidenceVerificationEngine()
        self.auditor = citation_auditor or CitationAuditor(verification_engine=self.engine)

    def evaluate_claim_cases(
        self,
        cases: list[dict[str, Any]],
    ) -> tuple[ClaimEvaluationMetricSummary, list[dict[str, Any]]]:
        """Evaluates verification accuracy and F1 over a list of gold standard test cases."""
        if not cases:
            return ClaimEvaluationMetricSummary(
                total_cases=0,
                correct_predictions=0,
                accuracy=0.0,
                macro_f1=0.0,
            ), []

        detailed_results: list[dict[str, Any]] = []
        statuses = [
            ClaimSupportStatus.SUPPORTED.value,
            ClaimSupportStatus.CONTRADICTED.value,
            ClaimSupportStatus.UNSUPPORTED.value,
        ]

        confusion_matrix: dict[str, int] = {}
        correct_count = 0

        for case in cases:
            claim_data = case["claim"]
            claim = (
                claim_data
                if isinstance(claim_data, NormalizedClaim)
                else NormalizedClaim(**claim_data)
            )
            passages = case.get("passages", [])
            expected_status = case["expected_status"]

            record: ClaimVerificationRecord = self.engine.verify_claim(claim, passages)

            # Map PARTIALLY_SUPPORTED to SUPPORTED if expected is supported for binary/ternary alignment
            predicted_status = record.status.value
            if (
                predicted_status == ClaimSupportStatus.PARTIALLY_SUPPORTED.value
                and expected_status == ClaimSupportStatus.SUPPORTED.value
            ):
                predicted_status = ClaimSupportStatus.SUPPORTED.value

            is_correct = predicted_status == expected_status
            if is_correct:
                correct_count += 1

            cm_key = f"{expected_status}->{predicted_status}"
            confusion_matrix[cm_key] = confusion_matrix.get(cm_key, 0) + 1

            detailed_results.append(
                {
                    "case_id": case.get("case_id"),
                    "claim_text": claim.text,
                    "expected": expected_status,
                    "predicted": predicted_status,
                    "is_correct": is_correct,
                    "confidence": record.confidence,
                    "rationale": record.rationale,
                }
            )

        total = len(cases)
        accuracy = round(correct_count / total, 4)

        # Compute per-status Precision, Recall, and F1
        per_status: dict[str, dict[str, float]] = {}
        f1_list: list[float] = []

        for st in statuses:
            tp = confusion_matrix.get(f"{st}->{st}", 0)
            fp = sum(
                confusion_matrix.get(f"{other}->{st}", 0) for other in statuses if other != st
            )
            fn = sum(
                confusion_matrix.get(f"{st}->{other}", 0) for other in statuses if other != st
            )

            precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
            recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
            f1 = (
                round(2.0 * precision * recall / (precision + recall), 4)
                if (precision + recall) > 0
                else 0.0
            )

            per_status[st] = {
                "true_positives": float(tp),
                "false_positives": float(fp),
                "false_negatives": float(fn),
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
            f1_list.append(f1)

        macro_f1 = round(sum(f1_list) / len(f1_list), 4) if f1_list else 0.0

        # Hallucination recall is recall on UNSUPPORTED claims
        hallucination_recall = per_status.get(ClaimSupportStatus.UNSUPPORTED.value, {}).get(
            "recall", 0.0
        )
        # Contradiction recall is recall on CONTRADICTED claims
        contradiction_recall = per_status.get(ClaimSupportStatus.CONTRADICTED.value, {}).get(
            "recall", 0.0
        )

        summary = ClaimEvaluationMetricSummary(
            total_cases=total,
            correct_predictions=correct_count,
            accuracy=accuracy,
            macro_f1=macro_f1,
            hallucination_detection_recall=hallucination_recall,
            contradiction_detection_recall=contradiction_recall,
            per_status_metrics=per_status,
            confusion_matrix=confusion_matrix,
        )
        return summary, detailed_results

    def audit_report_markdown(
        self,
        report_title: str,
        report_markdown: str,
        referenced_evidence: list[dict[str, Any]],
        tenant_id: str = "default",
    ) -> CitationVerificationResult:
        """Audits a complete markdown research report for citation resolution and claim faithfulness."""
        request = CitationVerificationRequest(
            tenant_id=tenant_id,
            report_title=report_title,
            report_markdown=report_markdown,
            referenced_evidence=referenced_evidence,
        )
        return self.auditor.audit_report(request)
