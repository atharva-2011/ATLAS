"""Comprehensive unit and integration tests for Phase 6 LLM Provider Abstraction and Structured Outputs."""

import pytest
from agent_runtime.core.config import Settings
from agent_runtime.llm.base import (
    LLMOutputParsingError,
)
from agent_runtime.llm.factory import ResilientLLMService
from agent_runtime.llm.mock_provider import MockLLMProvider
from agent_runtime.llm.parser import extract_json_from_text, parse_structured_output, redact_secrets
from agent_runtime.main import create_app
from atlas_contracts.agent_schemas import (
    CriticOutput,
    LLMMessage,
    LLMMessageRole,
    PlannerOutput,
    ResearcherOutput,
    SynthesizerOutput,
    VerifierOutput,
)
from fastapi.testclient import TestClient

# ============================================================================
# 1. Output Parser & Sanitizer Tests
# ============================================================================


def test_extract_json_from_markdown():
    text = """Here is the resulting plan:
```json
{
  "query": "test query",
  "plan_summary": "summary",
  "scope_dimensions": [],
  "subtasks": [
    {
      "task_id": "t1",
      "objective": "Check bounds",
      "agent_type": "document_researcher",
      "dependencies": [],
      "search_queries": [],
      "success_criteria": "done"
    }
  ],
  "estimated_depth": "medium"
}
```
Hope this helps!"""
    extracted = extract_json_from_text(text)
    assert extracted.startswith("{") and extracted.endswith("}")

    parsed = parse_structured_output(text, PlannerOutput)
    assert parsed.query == "test query"
    assert len(parsed.subtasks) == 1


def test_parse_structured_output_malformed_json_raises():
    invalid_text = "This is not json at all."
    with pytest.raises(LLMOutputParsingError) as exc_info:
        parse_structured_output(invalid_text, PlannerOutput)
    assert "Invalid JSON" in str(exc_info.value)


def test_parse_structured_output_invalid_schema_raises():
    invalid_schema = '{"query": 12345}'
    with pytest.raises(LLMOutputParsingError) as exc_info:
        parse_structured_output(invalid_schema, PlannerOutput)
    assert "Schema validation failed" in str(exc_info.value)


def test_redact_secrets():
    raw = "Header Authorization: Bearer sk-1234567890abcdef1234567890 or api_key=secretkey123456"
    sanitized = redact_secrets(raw)
    assert "sk-1234567890abcdef1234567890" not in sanitized
    assert "secretkey123456" not in sanitized
    assert "[REDACTED" in sanitized


# ============================================================================
# 2. Mock Provider & Schema Conformance Tests
# ============================================================================


@pytest.mark.anyio
async def test_mock_provider_structured_outputs():
    provider = MockLLMProvider()
    messages = [LLMMessage(role=LLMMessageRole.USER, content="Analyze question")]

    # 1. Planner
    planner_res, _ = await provider.complete_structured(messages, PlannerOutput)
    assert isinstance(planner_res, PlannerOutput)
    assert len(planner_res.subtasks) >= 1
    assert planner_res.subtasks[0].objective

    # 2. Researcher
    res_out, _ = await provider.complete_structured(messages, ResearcherOutput)
    assert isinstance(res_out, ResearcherOutput)
    assert len(res_out.evidence_items) >= 1
    assert res_out.evidence_items[0].claim

    # 3. Verifier
    ver_out, _ = await provider.complete_structured(messages, VerifierOutput)
    assert isinstance(ver_out, VerifierOutput)
    assert len(ver_out.verified_claims) >= 1
    assert ver_out.overall_support_ratio >= 0.0

    # 4. Critic
    crit_out, _ = await provider.complete_structured(messages, CriticOutput)
    assert isinstance(crit_out, CriticOutput)
    assert crit_out.coverage_score > 0.0

    # 5. Synthesizer
    synth_out, _ = await provider.complete_structured(messages, SynthesizerOutput)
    assert isinstance(synth_out, SynthesizerOutput)
    assert len(synth_out.sections) >= 1


# ============================================================================
# 3. Resilient Service (Retries, Timeout, Fallback) Tests
# ============================================================================


@pytest.mark.anyio
async def test_resilient_service_fallback_on_primary_failure():
    primary = MockLLMProvider(model_name="primary-failing", should_timeout=True)
    fallback = MockLLMProvider(model_name="fallback-success")

    service = ResilientLLMService(
        primary_provider=primary,
        fallback_provider=fallback,
        max_retries=1,
        initial_backoff_seconds=0.01,
    )

    messages = [LLMMessage(role=LLMMessageRole.USER, content="Hello")]
    resp = await service.complete(messages, timeout=0.01)

    assert resp.model == "fallback-success"
    assert resp.provider == "mock"


@pytest.mark.anyio
async def test_resilient_service_structured_fallback():
    primary = MockLLMProvider(model_name="primary-failing", should_timeout=True)
    fallback = MockLLMProvider(model_name="fallback-success")

    service = ResilientLLMService(
        primary_provider=primary,
        fallback_provider=fallback,
        max_retries=1,
        initial_backoff_seconds=0.01,
    )

    messages = [LLMMessage(role=LLMMessageRole.USER, content="Plan research")]
    parsed, resp = await service.complete_structured(messages, PlannerOutput, timeout=0.01)

    assert isinstance(parsed, PlannerOutput)
    assert resp.model == "fallback-success"


# ============================================================================
# 4. Agent Runtime LLM API Endpoints
# ============================================================================


def test_api_complete_text():
    settings = Settings(default_provider="mock", default_model="test-mock")
    app = create_app(settings=settings)
    client = TestClient(app)

    payload = {
        "messages": [{"role": "user", "content": "Explain ATLAS microservices"}],
        "temperature": 0.0,
    }
    response = client.post("/api/v1/llm/complete", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Mock completion for:" in data["content"]
    assert data["provider"] == "mock"
    assert data["usage"]["total_tokens"] > 0


def test_api_complete_structured_planner():
    settings = Settings(default_provider="mock", default_model="test-mock")
    app = create_app(settings=settings)
    client = TestClient(app)

    payload = {
        "schema_type": "planner",
        "messages": [{"role": "user", "content": "Plan deep investigation into battery chemistry"}],
    }
    response = client.post("/api/v1/llm/complete-structured", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "parsed" in data
    assert data["parsed"]["query"] == "Target Query"
    assert len(data["parsed"]["subtasks"]) >= 1


def test_api_complete_structured_unknown_schema():
    settings = Settings(default_provider="mock")
    app = create_app(settings=settings)
    client = TestClient(app)

    payload = {
        "schema_type": "non_existent_role",
        "messages": [{"role": "user", "content": "Test"}],
    }
    response = client.post("/api/v1/llm/complete-structured", json=payload)
    assert response.status_code == 400
    assert "Unknown schema_type" in response.json()["detail"]
