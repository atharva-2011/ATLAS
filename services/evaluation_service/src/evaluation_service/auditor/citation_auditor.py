"""Citation resolution and faithfulness evaluation auditor."""

from atlas_contracts.evaluation import (
    CitationVerificationRequest,
    CitationVerificationResult,
    ClaimSupportStatus,
)
from evaluation_service.claims.normalizer import ClaimNormalizer, extract_inline_citations
from evaluation_service.verifier.engine import EvidenceVerificationEngine


class CitationAuditor:
    """Audits report citations, resolves IDs, and calculates faithfulness and precision."""

    def __init__(
        self,
        claim_normalizer: ClaimNormalizer | None = None,
        verification_engine: EvidenceVerificationEngine | None = None,
    ) -> None:
        self.normalizer = claim_normalizer or ClaimNormalizer()
        self.engine = verification_engine or EvidenceVerificationEngine()

    def audit_report(self, request: CitationVerificationRequest) -> CitationVerificationResult:
        # Step 1: Extract all inline citations
        cited_keys = extract_inline_citations(request.report_markdown)

        # Build index of known evidence IDs
        known_evidence_ids = set()
        for rec in request.referenced_evidence:
            eid = str(rec.get("evidence_id") or rec.get("chunk_id") or "")
            if eid:
                known_evidence_ids.add(eid)

        resolved_count = 0
        unresolved = []
        for k in cited_keys:
            if k in known_evidence_ids:
                resolved_count += 1
            else:
                unresolved.append(k)

        citation_precision = round(resolved_count / len(cited_keys), 3) if cited_keys else 1.0

        # Step 2: Extract normalized factual claims from markdown text
        claims = self.normalizer.extract_claims(request.report_markdown)

        # Step 3: Verify each claim against referenced evidence
        records = [self.engine.verify_claim(c, request.referenced_evidence) for c in claims]

        supported_count = sum(
            1
            for r in records
            if r.status in (ClaimSupportStatus.SUPPORTED, ClaimSupportStatus.PARTIALLY_SUPPORTED)
        )
        contradicted_count = sum(1 for r in records if r.status == ClaimSupportStatus.CONTRADICTED)
        unsupported_count = sum(1 for r in records if r.status == ClaimSupportStatus.UNSUPPORTED)

        faithfulness = round(supported_count / len(records), 3) if records else 1.0

        return CitationVerificationResult(
            total_citations=len(cited_keys),
            resolved_citations=resolved_count,
            unresolved_citations=unresolved,
            faithfulness_score=faithfulness,
            citation_precision=citation_precision,
            claims_evaluated=len(records),
            supported_claims_count=supported_count,
            contradicted_claims_count=contradicted_count,
            unsupported_claims_count=unsupported_count,
            records=records,
        )
