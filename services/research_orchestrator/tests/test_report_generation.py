"""Comprehensive unit and integration tests for Phase 10 Synthesis, Citations, and Publication-Grade Reporting."""

from atlas_contracts.agent_schemas import ReportSection, SynthesizerOutput
from research_orchestrator.reporting.citations import CitationResolver
from research_orchestrator.reporting.renderer import ReportRenderer

# ============================================================================
# 1. Citation Resolver Tests
# ============================================================================


def test_citation_resolver_maps_known_evidence():
    resolver = CitationResolver()
    evidence_records = [
        {
            "evidence_id": "ev_perf_01",
            "document_id": "d1",
            "title": "Autonomous Systems Benchmark 2026",
            "publisher": "Robotics Research Institute",
            "source_passage": "Empirical testing validated p95 reaction latency of 18 milliseconds.",
            "locator": {"page": 14, "section": "Control Loop Performance"},
        },
        {
            "evidence_id": "ev_web_02",
            "source_type": "web",
            "title": "Global Edge Computing Survey",
            "url": "https://edge-survey.org/2026",
            "publisher": "Edge Computing Forum",
            "source_passage": "Industrial deployments report 40% reduction in bandwidth overhead.",
        },
    ]

    # Resolve document reference
    ref1 = resolver.resolve_reference("ev_perf_01", evidence_records)
    assert ref1 is not None
    assert ref1.citation_key == "ev_perf_01"
    assert ref1.title == "Autonomous Systems Benchmark 2026"
    assert "Page: 14" in (ref1.locator_label or "")
    assert "18 milliseconds" in ref1.exact_excerpt

    # Resolve web reference
    ref2 = resolver.resolve_reference("ev_web_02", evidence_records)
    assert ref2 is not None
    assert ref2.source_type == "web"
    assert ref2.url == "https://edge-survey.org/2026"

    # Build bibliography with unresolvable reference fallback
    bib = resolver.build_bibliography(
        ["ev_perf_01", "ev_web_02", "ev_missing_99"], evidence_records
    )
    assert len(bib) == 3
    assert bib[0].citation_key == "ev_perf_01"
    assert bib[1].citation_key == "ev_web_02"
    assert bib[2].source_type == "unresolved"


# ============================================================================
# 2. Publication-Grade Markdown Renderer Tests
# ============================================================================


def test_report_renderer_generates_complete_publication_markdown():
    renderer = ReportRenderer()
    synth_output = SynthesizerOutput(
        title="Comprehensive Analysis of Next-Generation Edge Compute Architectures",
        executive_summary="Edge computing nodes achieve localized autonomy while maintaining strict latency boundaries.",
        sections=[
            ReportSection(
                title="1. Latency & Determinism",
                content="Empirical validation established sub-20ms control loop latency under stress [ev_perf_01].",
                cited_evidence_ids=["ev_perf_01"],
            ),
            ReportSection(
                title="2. Bandwidth Conservation",
                content="Localized edge filtering delivered substantial bandwidth savings [ev_web_02].",
                cited_evidence_ids=["ev_web_02"],
            ),
        ],
        limitations=[
            "Testing performed in simulated electromagnetic interference environments.",
        ],
        full_markdown="",
        total_citations=2,
    )

    evidence_records = [
        {
            "evidence_id": "ev_perf_01",
            "title": "Autonomous Systems Benchmark 2026",
            "publisher": "Robotics Research Institute",
            "source_passage": "Empirical testing validated p95 reaction latency of 18 milliseconds.",
            "locator": {"page": 14},
        },
        {
            "evidence_id": "ev_web_02",
            "source_type": "web",
            "title": "Global Edge Computing Survey",
            "url": "https://edge-survey.org/2026",
            "publisher": "Edge Computing Forum",
            "source_passage": "Industrial deployments report 40% reduction in bandwidth overhead.",
        },
    ]

    gaps = [{"description": "Missing evaluation on extreme thermal fluctuations (-40C to 85C)."}]
    contras = ["Power efficiency metrics varied between lab benchmarks and field telemetry."]

    markdown = renderer.render_markdown(
        research_id="run_test_888",
        query="Analyze edge compute latency and bandwidth efficiency",
        synth_output=synth_output,
        evidence_records=evidence_records,
        critic_gaps=gaps,
        contradictions=contras,
    )

    # Verifications
    assert "# Comprehensive Analysis of Next-Generation Edge Compute Architectures" in markdown
    assert "## Executive Summary" in markdown
    assert "## 1. Latency & Determinism" in markdown
    assert "## 2. Bandwidth Conservation" in markdown
    assert "## Scope & Methodology" in markdown
    assert "### Limitations & Research Gaps" in markdown
    assert "Unresolved Gap:" in markdown
    assert "### Contradictions & Disagreements" in markdown
    assert "## References & Evidence Provenance" in markdown
    assert "[ev_perf_01]" in markdown
    assert "[ev_web_02]" in markdown
    assert "Autonomous Systems Benchmark 2026" in markdown
    assert "https://edge-survey.org/2026" in markdown
