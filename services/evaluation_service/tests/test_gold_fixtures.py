"""Unit tests verifying the integrity and valid format of ATLAS gold standard benchmark fixtures."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "gold_sets"


def test_retrieval_gold_set_structure() -> None:
    path = FIXTURES_DIR / "retrieval_gold_set.json"
    assert path.exists(), f"Missing gold set file: {path}"

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert "corpus" in data and len(data["corpus"]) >= 5
    assert "queries" in data and len(data["queries"]) >= 5

    for c in data["corpus"]:
        assert "chunk_id" in c
        assert "text" in c
        assert "document_id" in c

    for q in data["queries"]:
        assert "query_id" in q
        assert "query" in q
        assert "relevant_chunk_ids" in q
        assert isinstance(q["relevant_chunk_ids"], list)
        assert len(q["relevant_chunk_ids"]) > 0


def test_claim_verification_gold_set_structure() -> None:
    path = FIXTURES_DIR / "claim_verification_gold_set.json"
    assert path.exists(), f"Missing gold set file: {path}"

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert "test_cases" in data and len(data["test_cases"]) >= 4

    for case in data["test_cases"]:
        assert "case_id" in case
        assert "claim" in case
        assert "expected_status" in case
        assert case["expected_status"] in (
            "supported",
            "partially_supported",
            "contradicted",
            "unsupported",
        )
        assert "passages" in case


def test_research_scenarios_structure() -> None:
    path = FIXTURES_DIR / "research_scenarios.json"
    assert path.exists(), f"Missing gold set file: {path}"

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert "scenarios" in data and len(data["scenarios"]) >= 1

    for sc in data["scenarios"]:
        assert "scenario_id" in sc
        assert "golden_report_markdown" in sc
        assert "corrupted_report_markdown" in sc
        assert "referenced_evidence" in sc
