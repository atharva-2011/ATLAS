"""Citation resolver and bibliography compiler for research report generation."""

from typing import Any

from pydantic import BaseModel


class CitationReference(BaseModel):
    """Structured bibliographic reference linked to a cited evidence item."""

    citation_key: str
    evidence_id: str
    source_type: str  # internal_document | web | paper
    title: str
    publisher_or_document: str
    url: str | None = None
    locator_label: str | None = None
    retrieved_at_iso: str | None = None
    exact_excerpt: str


class CitationResolver:
    """Resolves inline citation tags in report markdown and constructs an authenticated bibliography."""

    def resolve_reference(
        self,
        citation_key: str,
        evidence_records: list[dict[str, Any]],
    ) -> CitationReference | None:
        """Find matching evidence item and format bibliographic reference."""
        for ev in evidence_records:
            eid = str(ev.get("evidence_id") or ev.get("chunk_id") or "")
            if eid == citation_key:
                locator = ev.get("locator", {})
                locator_parts = (
                    [f"{k.capitalize()}: {v}" for k, v in locator.items()] if locator else []
                )
                locator_label = ", ".join(locator_parts) if locator_parts else None

                source_type = ev.get("source_type", "internal_document")
                title = ev.get("title") or (
                    f"Internal Document ({ev.get('document_id')})"
                    if ev.get("document_id")
                    else "Primary Research Document"
                )
                publisher = ev.get("publisher") or (
                    "ATLAS Knowledge Index"
                    if source_type == "internal_document"
                    else "External Web Source"
                )

                return CitationReference(
                    citation_key=citation_key,
                    evidence_id=eid,
                    source_type=source_type,
                    title=title,
                    publisher_or_document=publisher,
                    url=ev.get("url"),
                    locator_label=locator_label,
                    retrieved_at_iso=ev.get("retrieved_at"),
                    exact_excerpt=ev.get("source_passage")
                    or ev.get("passage")
                    or ev.get("text", ""),
                )
        return None

    def build_bibliography(
        self,
        cited_keys: list[str],
        evidence_records: list[dict[str, Any]],
    ) -> list[CitationReference]:
        """Compile verified citation references in order of citation appearance."""
        resolved: list[CitationReference] = []
        seen = set()

        for k in cited_keys:
            if k in seen:
                continue
            ref = self.resolve_reference(k, evidence_records)
            if ref:
                resolved.append(ref)
                seen.add(k)
            else:
                # Ghost reference fallback
                resolved.append(
                    CitationReference(
                        citation_key=k,
                        evidence_id=k,
                        source_type="unresolved",
                        title=f"Unresolved Citation [{k}]",
                        publisher_or_document="Unknown / Missing Reference",
                        exact_excerpt="",
                    )
                )
                seen.add(k)

        return resolved
