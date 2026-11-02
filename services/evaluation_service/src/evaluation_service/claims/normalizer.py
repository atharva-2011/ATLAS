"""Claim normalizer extracting atomic factual propositions and identifying opinion/speculation."""

import re
from uuid import uuid4

from atlas_contracts.evaluation import NormalizedClaim


def extract_inline_citations(text: str) -> list[str]:
    """Find all citation keys matching [ev_...] or [c_...] or [doc_...]."""
    matches = re.findall(r"\[([a-zA-Z0-9_\-]+)\]", text)
    return list(dict.fromkeys(matches))


class ClaimNormalizer:
    """Decomposes unstructured or markdown text into atomic, checkable factual claims."""

    OPINION_MARKERS = (
        "we believe",
        "in our opinion",
        "might",
        "could perhaps",
        "it is possible",
        "speculatively",
        "we recommend",
        "suggests that",
    )

    def normalize_sentence(self, sentence: str) -> NormalizedClaim:
        cleaned = sentence.strip()
        citations = extract_inline_citations(cleaned)
        # Strip brackets from statement text for clean verification
        text_no_citations = re.sub(r"\[[a-zA-Z0-9_\-]+\]", "", cleaned).strip()

        is_opinion = any(m in text_no_citations.lower() for m in self.OPINION_MARKERS)

        return NormalizedClaim(
            claim_id=f"claim_{uuid4().hex[:6]}",
            text=text_no_citations,
            is_opinion_or_analysis=is_opinion,
            cited_evidence_ids=citations,
        )

    def extract_claims(self, text: str) -> list[NormalizedClaim]:
        """Split text into sentences and yield normalized claim objects."""
        # Simple sentence splitter preserving abbreviations
        sentences = re.split(r"(?<=[.!?])\s+", text)
        claims: list[NormalizedClaim] = []

        for s in sentences:
            trimmed = s.strip()
            # Ignore headers, list markers, or very short fragments
            if len(trimmed) < 10 or trimmed.startswith("#") or trimmed.startswith("---"):
                continue
            claims.append(self.normalize_sentence(trimmed))

        return claims
