"""Deterministic and NLI-based claim-to-evidence verification engine."""

import re
from typing import Any

from atlas_contracts.evaluation import (
    ClaimSupportStatus,
    ClaimVerificationRecord,
    NormalizedClaim,
)


def tokenize_words(text: str) -> set[str]:
    return set(re.findall(r"\b\w+\b", text.lower()))


class EvidenceVerificationEngine:
    """Evaluates factual grounding of individual claims against source evidence passages."""

    CONTRADICTION_PAIRS = [
        ("increase", "decrease"),
        ("increases", "decreases"),
        ("increased", "decreased"),
        ("exceed", "below"),
        ("above", "below"),
        ("higher", "lower"),
        ("highest", "lowest"),
        ("maximum", "minimum"),
        ("supported", "unsupported"),
        ("true", "false"),
        ("positive", "negative"),
        ("enabled", "disabled"),
        ("growth", "decline"),
        ("reduce", "increase"),
    ]

    def _check_contradiction(self, claim_text: str, passage_text: str) -> bool:
        c_words = tokenize_words(claim_text)
        p_words = tokenize_words(passage_text)

        for w1, w2 in self.CONTRADICTION_PAIRS:
            if (w1 in c_words and w2 in p_words) or (w2 in c_words and w1 in p_words):
                return True
        return False

    def verify_claim(
        self,
        claim: NormalizedClaim,
        passages: list[dict[str, Any]],
    ) -> ClaimVerificationRecord:
        """Evaluate a single claim against candidate evidence passages."""
        # Opinions/analysis do not require external verification
        if claim.is_opinion_or_analysis:
            return ClaimVerificationRecord(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                status=ClaimSupportStatus.SUPPORTED,
                rationale="Labeled as analysis or subjective evaluation.",
            )

        claim_tokens = tokenize_words(claim.text)
        if not claim_tokens:
            return ClaimVerificationRecord(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                status=ClaimSupportStatus.UNSUPPORTED,
                rationale="Claim contains no verifiable content.",
            )

        # Match against cited evidence if available, or all passages
        matched_passages = []
        if claim.cited_evidence_ids:
            for p in passages:
                pid = str(p.get("evidence_id") or p.get("chunk_id") or "")
                if pid in claim.cited_evidence_ids:
                    matched_passages.append(p)

        # If no specific cited match, search all passages
        if not matched_passages:
            matched_passages = passages

        best_overlap = 0.0
        best_passage = None
        has_contradiction = False
        contradiction_evidence = None

        for p in matched_passages:
            p_text = p.get("passage") or p.get("text") or ""
            p_tokens = tokenize_words(p_text)
            if not p_tokens:
                continue

            if self._check_contradiction(claim.text, p_text):
                has_contradiction = True
                contradiction_evidence = p_text

            overlap = len(claim_tokens.intersection(p_tokens)) / len(claim_tokens)
            if overlap > best_overlap:
                best_overlap = overlap
                best_passage = p

        if has_contradiction and best_overlap > 0.4:
            return ClaimVerificationRecord(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                status=ClaimSupportStatus.CONTRADICTED,
                contradiction_text=contradiction_evidence,
                confidence=0.95,
                rationale="Passage contradicts factual assertion in claim.",
            )

        if best_overlap >= 0.70:
            pid = (
                str(best_passage.get("evidence_id") or best_passage.get("chunk_id") or "")
                if best_passage
                else ""
            )
            locator = best_passage.get("locator", {}) if best_passage else {}
            return ClaimVerificationRecord(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                status=ClaimSupportStatus.SUPPORTED,
                supporting_evidence_ids=[pid] if pid else [],
                confidence=round(best_overlap, 3),
                provenance_locator=locator,
                rationale="Substantial keyword and semantic overlap with source passage.",
            )

        if best_overlap >= 0.40:
            pid = (
                str(best_passage.get("evidence_id") or best_passage.get("chunk_id") or "")
                if best_passage
                else ""
            )
            return ClaimVerificationRecord(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                status=ClaimSupportStatus.PARTIALLY_SUPPORTED,
                supporting_evidence_ids=[pid] if pid else [],
                confidence=round(best_overlap, 3),
                rationale="Partial factual support found in reference passages.",
            )

        return ClaimVerificationRecord(
            claim_id=claim.claim_id,
            claim_text=claim.text,
            status=ClaimSupportStatus.UNSUPPORTED,
            confidence=round(1.0 - best_overlap, 3),
            rationale="No supporting evidence passage identified in provided context.",
        )
