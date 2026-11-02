"""Publication-grade Markdown report renderer formatting structured intelligence reports."""

from datetime import UTC, datetime
from typing import Any

from atlas_contracts.agent_schemas import SynthesizerOutput

from research_orchestrator.reporting.citations import CitationReference, CitationResolver


class ReportRenderer:
    """Renders structured SynthesizerOutput and bibliographies into clean Markdown artifacts."""

    def __init__(self, citation_resolver: CitationResolver | None = None) -> None:
        self.resolver = citation_resolver or CitationResolver()

    def render_markdown(
        self,
        research_id: str,
        query: str,
        synth_output: SynthesizerOutput,
        evidence_records: list[dict[str, Any]],
        critic_gaps: list[dict[str, Any]] | None = None,
        contradictions: list[str] | None = None,
    ) -> str:
        now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        gaps = critic_gaps or []
        contras = contradictions or []

        # 1. Collect all cited keys in order
        all_cited_keys: list[str] = []
        for sec in synth_output.sections:
            all_cited_keys.extend(sec.cited_evidence_ids)

        # 2. Build verified bibliography
        bibliography: list[CitationReference] = self.resolver.build_bibliography(
            cited_keys=all_cited_keys,
            evidence_records=evidence_records,
        )

        # 3. Assemble document markdown
        doc = [
            f"# {synth_output.title}",
            "",
            "> **ATLAS Multi-Agent Research Intelligence System**",
            f"> *Research Run ID:* `{research_id}` | *Generated:* {now_str}",
            f"> *Research Objective:* {query}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            synth_output.executive_summary,
            "",
            "---",
            "",
        ]

        # 4. Body Sections
        for sec in synth_output.sections:
            doc.append(f"## {sec.title}")
            doc.append("")
            doc.append(sec.content)
            doc.append("")

        # 5. Methodological Scope & Limitations
        doc.append("---")
        doc.append("")
        doc.append("## Scope & Methodology")
        doc.append("")
        doc.append(
            "- **Investigation Path:** Automated multi-agent retrieval across internal vector/sparse indices and external sources."
        )
        doc.append(
            "- **Grounding Integrity:** All factual claims audited with claim-to-passage alignment and NLI contradiction checks."
        )
        doc.append(
            f"- **Sources Consulted:** {len(evidence_records)} atomic evidence passages retrieved and indexed."
        )
        doc.append("")

        if synth_output.limitations or gaps:
            doc.append("### Limitations & Research Gaps")
            doc.append("")
            for lim in synth_output.limitations:
                doc.append(f"- {lim}")
            for gap in gaps:
                desc = gap.get("description") if isinstance(gap, dict) else str(gap)
                doc.append(f"- **Unresolved Gap:** {desc}")
            doc.append("")

        if contras:
            doc.append("### Contradictions & Disagreements")
            doc.append("")
            doc.append(
                "The following claims exhibited conflicting evidence across consulted sources:"
            )
            for c in contras:
                doc.append(f"- *Contradiction:* {c}")
            doc.append("")

        # 6. References & Bibliography
        doc.append("---")
        doc.append("")
        doc.append("## References & Evidence Provenance")
        doc.append("")

        if not bibliography:
            doc.append("*No citations registered in this report.*")
        else:
            for idx, ref in enumerate(bibliography, start=1):
                loc = f" ({ref.locator_label})" if ref.locator_label else ""
                url_str = f" | [Source Link]({ref.url})" if ref.url else ""
                doc.append(
                    f"{idx}. **[{ref.citation_key}]** *{ref.title}*{loc}. {ref.publisher_or_document}{url_str}"
                )
                if ref.exact_excerpt:
                    clean_excerpt = ref.exact_excerpt.replace("\n", " ").strip()[:200]
                    doc.append(f'   > "{clean_excerpt}..."')
                doc.append("")

        return "\n".join(doc)
