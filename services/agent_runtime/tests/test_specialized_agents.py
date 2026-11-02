"""Comprehensive tests for Phase 7 Specialized Research Agents."""

import pytest
from agent_runtime.agents.base import AgentToolPermission
from agent_runtime.agents.critic import CriticAgent
from agent_runtime.agents.document_researcher import DocumentResearcherAgent
from agent_runtime.agents.planner import PlannerAgent
from agent_runtime.agents.registry import AgentRegistry
from agent_runtime.agents.synthesizer import SynthesizerAgent
from agent_runtime.agents.verifier import EvidenceVerifierAgent
from agent_runtime.agents.web_researcher import WebResearcherAgent, WebSearchAdapter
from agent_runtime.core.config import Settings
from agent_runtime.llm.mock_provider import MockLLMProvider
from agent_runtime.main import create_app
from atlas_contracts.agent_schemas import AgentInput
from fastapi.testclient import TestClient

# ============================================================================
# 1. Tool Permissions Audit
# ============================================================================


def test_agent_tool_permissions():
    assert "retrieval_service_hybrid_search" in AgentToolPermission.DOCUMENT_RESEARCHER_TOOLS
    assert "web_search" in AgentToolPermission.WEB_RESEARCHER_TOOLS
    # Check that document researcher cannot do web search
    assert "web_search" not in AgentToolPermission.DOCUMENT_RESEARCHER_TOOLS
    assert "citation_match" in AgentToolPermission.VERIFIER_TOOLS


# ============================================================================
# 2. Individual Specialized Agent Executions (Offline / Deterministic)
# ============================================================================


@pytest.mark.anyio
async def test_planner_agent_run():
    provider = MockLLMProvider()
    agent = PlannerAgent(llm_provider=provider)

    payload = AgentInput(
        task_id="t_plan_1",
        objective="Analyze performance limits of solid-state batteries in EVs",
        agent_type="planner",
    )
    result = await agent.run(payload)

    assert result.status == "completed"
    assert result.agent_type == "planner"
    assert result.task_id == "t_plan_1"
    assert result.output["query"] == "Analyze performance limits of solid-state batteries in EVs"
    assert len(result.output["subtasks"]) >= 1


@pytest.mark.anyio
async def test_document_researcher_with_mock_retrieval():
    provider = MockLLMProvider()
    mock_chunks = [
        {
            "chunk_id": "c_battery_01",
            "text": "Solid-state silicon anodes achieve energy density exceeding 450 Wh/kg.",
            "locator": {"page": 12, "section": "Energy Density"},
        }
    ]
    agent = DocumentResearcherAgent(
        llm_provider=provider,
        mock_retrieval_response=mock_chunks,
    )

    payload = AgentInput(
        task_id="t_doc_1",
        objective="Extract battery energy density metrics",
        agent_type="document_researcher",
        tenant_id="test-tenant",
    )
    result = await agent.run(payload)

    assert result.status == "completed"
    assert result.output["sources_consulted"] == 1
    assert len(result.output["evidence_items"]) >= 1
    evidence = result.output["evidence_items"][0]
    assert evidence["claim"]
    assert evidence["source_passage"]


@pytest.mark.anyio
async def test_web_researcher_agent_run():
    provider = MockLLMProvider()
    mock_web = [
        {
            "url": "https://battery-tech.org/report-2026",
            "title": "Battery Breakthroughs 2026",
            "snippet": "Silicon electrolyte prototypes display 80% charge retention over 1000 cycles.",
            "publisher": "Tech Journal",
        }
    ]
    search_adapter = WebSearchAdapter(mock_results=mock_web)
    agent = WebResearcherAgent(llm_provider=provider, search_adapter=search_adapter)

    payload = AgentInput(
        task_id="t_web_1",
        objective="Find latest cycle retention benchmarks",
        agent_type="web_researcher",
        search_queries=["silicon electrolyte cycle retention"],
    )
    result = await agent.run(payload)

    assert result.status == "completed"
    assert result.output["sources_consulted"] == 1
    assert len(result.output["evidence_items"]) >= 1
    assert result.output["evidence_items"][0]["source_type"] == "web"
    assert result.output["evidence_items"][0]["url"] == "https://battery-tech.org/report-2026"


@pytest.mark.anyio
async def test_evidence_verifier_agent_run():
    provider = MockLLMProvider()
    agent = EvidenceVerifierAgent(llm_provider=provider)

    payload = AgentInput(
        task_id="t_ver_1",
        objective="Verify factual grounding of claims",
        agent_type="evidence_verifier",
        context_data={
            "evidence_items": [
                {
                    "evidence_id": "ev_1",
                    "claim": "P95 latency is under 50ms.",
                    "source_passage": "Empirical tests demonstrated p95 response times remaining strictly below 50ms.",
                }
            ]
        },
    )
    result = await agent.run(payload)

    assert result.status == "completed"
    assert result.output["total_claims"] == 1
    assert len(result.output["verified_claims"]) == 1
    assert result.output["verified_claims"][0]["verdict"] == "supported"


@pytest.mark.anyio
async def test_critic_agent_run():
    provider = MockLLMProvider()
    agent = CriticAgent(llm_provider=provider)

    payload = AgentInput(
        task_id="t_crit_1",
        objective="Audit research coverage",
        agent_type="critic",
        context_data={
            "subtasks": ["Check hardware bounds", "Verify market metrics"],
            "evidence_items": [{"evidence_id": "ev_1", "claim": "Valid claim"}],
        },
    )
    result = await agent.run(payload)

    assert result.status == "completed"
    assert result.output["coverage_score"] > 0.0
    assert result.output["recommendation"] == "proceed"


@pytest.mark.anyio
async def test_synthesizer_agent_run():
    provider = MockLLMProvider()
    agent = SynthesizerAgent(llm_provider=provider)

    payload = AgentInput(
        task_id="t_synth_1",
        objective="Synthesize final research report",
        agent_type="synthesizer",
        context_data={
            "verified_evidence": [
                {
                    "evidence_id": "ev_mock_1",
                    "claim": "P95 latency is strictly under 50ms.",
                    "source_passage": "Empirical tests demonstrated p95 response times remaining strictly below 50ms.",
                    "source_type": "internal_document",
                }
            ]
        },
    )
    result = await agent.run(payload)

    assert result.status == "completed"
    assert result.output["title"]
    assert len(result.output["sections"]) >= 1
    assert result.evidence_count >= 1


# ============================================================================
# 3. Agent Registry & API Dispatch Endpoints
# ============================================================================


def test_agent_registry_lookup():
    provider = MockLLMProvider()
    registry = AgentRegistry(llm_provider=provider)

    roles = registry.list_available_agents()
    assert "planner" in roles
    assert "document_researcher" in roles
    assert "web_researcher" in roles
    assert "evidence_verifier" in roles
    assert "critic" in roles
    assert "synthesizer" in roles

    planner = registry.get_agent("planner")
    assert planner.agent_type == "planner"

    with pytest.raises(KeyError):
        registry.get_agent("unknown_alien_agent")


def test_api_list_roles():
    settings = Settings(default_provider="mock")
    app = create_app(settings=settings)
    client = TestClient(app)

    response = client.get("/api/v1/agents/roles")
    assert response.status_code == 200
    roles = response.json()
    assert "planner" in roles
    assert "document_researcher" in roles
    assert "synthesizer" in roles


def test_api_dispatch_planner():
    settings = Settings(default_provider="mock")
    app = create_app(settings=settings)
    client = TestClient(app)

    payload = {
        "task_id": "api_task_1",
        "objective": "Investigate aerospace composite material endurance",
        "agent_type": "planner",
    }
    response = client.post("/api/v1/agents/dispatch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["task_id"] == "api_task_1"
    assert data["agent_type"] == "planner"
    assert len(data["output"]["subtasks"]) >= 1


def test_api_dispatch_unknown_role_raises_400():
    settings = Settings(default_provider="mock")
    app = create_app(settings=settings)
    client = TestClient(app)

    payload = {
        "task_id": "api_task_err",
        "objective": "Test",
        "agent_type": "unknown_role",
    }
    response = client.post("/api/v1/agents/dispatch", json=payload)
    assert response.status_code == 400
    assert "Unknown agent type" in response.json()["detail"]
