from uuid import uuid4

import pytest
from atlas_contracts.agent_schemas import AgentInput, AgentResult
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver
from research_orchestrator.api.workflow_routes import get_workflow_runner
from research_orchestrator.core.config import Settings
from research_orchestrator.main import create_app
from research_orchestrator.workflow.agent_client import AgentRuntimeClient
from research_orchestrator.workflow.graph import (
    should_continue_after_intake,
    should_continue_after_planning,
    should_retry_or_synthesize,
)
from research_orchestrator.workflow.runner import ResearchWorkflowRunner
from research_orchestrator.workflow.state import ResearchWorkflowState


class MockAgentClient(AgentRuntimeClient):
    """Mock agent client providing conforming responses for workflow testing."""

    async def dispatch(self, payload: AgentInput) -> AgentResult:
        if payload.agent_type == "planner":
            return AgentResult(
                task_id=payload.task_id,
                agent_type="planner",
                status="completed",
                output={
                    "query": payload.objective,
                    "plan_summary": "Test plan",
                    "subtasks": [
                        {
                            "task_id": "st1",
                            "objective": "Subtask objective",
                            "agent_type": "document_researcher",
                            "success_criteria": "done",
                        }
                    ],
                },
            )
        if payload.agent_type in ("document_researcher", "web_researcher"):
            return AgentResult(
                task_id=payload.task_id,
                agent_type=payload.agent_type,
                status="completed",
                output={
                    "task_id": payload.task_id,
                    "summary_findings": "Findings",
                    "evidence_items": [
                        {
                            "evidence_id": f"ev_{payload.task_id}",
                            "claim": "Test claim",
                            "source_passage": "Source passage excerpt",
                            "source_type": "internal_document",
                        }
                    ],
                    "sources_consulted": 1,
                },
            )
        if payload.agent_type == "evidence_verifier":
            return AgentResult(
                task_id=payload.task_id,
                agent_type="evidence_verifier",
                status="completed",
                output={
                    "total_claims": 1,
                    "verified_claims": [
                        {
                            "claim": "Test claim",
                            "evidence_id": "ev_st1",
                            "verdict": "supported",
                            "rationale": "Direct match",
                        }
                    ],
                },
            )
        if payload.agent_type == "critic":
            return AgentResult(
                task_id=payload.task_id,
                agent_type="critic",
                status="completed",
                output={
                    "coverage_score": 0.95,
                    "is_sufficient": True,
                    "gaps": [],
                    "recommendation": "proceed",
                },
            )
        if payload.agent_type == "synthesizer":
            return AgentResult(
                task_id=payload.task_id,
                agent_type="synthesizer",
                status="completed",
                output={
                    "title": "Synthesis Report",
                    "executive_summary": "Executive Summary",
                    "sections": [
                        {
                            "title": "Findings",
                            "content": "Evidence report [ev_st1]",
                            "cited_evidence_ids": ["ev_st1"],
                        }
                    ],
                    "full_markdown": "# Synthesis Report",
                },
            )
        return AgentResult(
            task_id=payload.task_id,
            agent_type=payload.agent_type,
            status="completed",
            output={},
        )


# ============================================================================
# 1. Conditional Edge Unit Tests
# ============================================================================


def test_conditional_edges():
    state_valid: ResearchWorkflowState = {
        "research_id": "r1",
        "tenant_id": "t1",
        "query": "Valid research question",
        "max_retries": 1,
        "retry_count": 0,
        "thread_id": "th1",
        "status": "planning",
        "iteration": 1,
        "planned_subtasks": [{"task_id": "st1"}],
        "completed_task_ids": [],
        "accumulated_evidence": [],
        "verified_evidence": [],
        "unverified_claims": [],
        "critic_gaps": [],
        "contradictions": [],
        "final_report": None,
        "error": None,
    }

    assert should_continue_after_intake(state_valid) == "planning"
    assert should_continue_after_planning(state_valid) == "parallel_research"
    assert should_retry_or_synthesize(state_valid) == "synthesis"

    # Test failure edge
    state_fail = dict(state_valid)
    state_fail["status"] = "failed"
    state_fail["error"] = "Error"
    assert should_continue_after_intake(state_fail) == "failed"

    # Test retry branch when gaps exist and budget remains
    state_retry = dict(state_valid)
    state_retry["status"] = "evaluating_retry"
    state_retry["critic_gaps"] = [{"gap_id": "g1", "description": "Need more data"}]
    state_retry["retry_count"] = 0
    state_retry["max_retries"] = 1
    assert should_retry_or_synthesize(state_retry) == "parallel_research"
    assert state_retry["retry_count"] == 1


# ============================================================================
# 2. End-to-End Workflow Graph Execution Tests
# ============================================================================


@pytest.mark.anyio
async def test_research_workflow_full_run():
    client = MockAgentClient()
    checkpointer = MemorySaver()
    runner = ResearchWorkflowRunner(agent_client=client, checkpointer=checkpointer)

    query = "Investigate next-generation solid-state battery electrolytes"
    final_state = await runner.execute_run(query=query)

    assert final_state["status"] == "completed"
    assert len(final_state["planned_subtasks"]) >= 1
    assert len(final_state["completed_task_ids"]) >= 1
    assert len(final_state["accumulated_evidence"]) >= 1
    assert final_state["final_report"] is not None
    assert final_state["final_report"]["title"]
    assert len(final_state["final_report"]["sections"]) >= 1


@pytest.mark.anyio
async def test_checkpoint_state_inspection():
    client = MockAgentClient()
    checkpointer = MemorySaver()
    runner = ResearchWorkflowRunner(agent_client=client, checkpointer=checkpointer)

    thread_id = f"custom_thread_{uuid4().hex[:6]}"
    final_state = await runner.execute_run(
        query="Examine quantum dot displays efficiency limits",
        thread_id=thread_id,
    )
    assert final_state["status"] == "completed"

    # Inspect checkpoint saved in checkpointer
    config = {"configurable": {"thread_id": thread_id}}
    checkpoint_tuple = checkpointer.get_tuple(config)
    assert checkpoint_tuple is not None
    checkpoint_state = checkpoint_tuple.checkpoint
    assert checkpoint_state is not None


# ============================================================================
# 3. Workflow API Execution Route Tests
# ============================================================================


def test_api_workflow_execution():
    settings = Settings()
    app = create_app(settings=settings)
    client_mock = MockAgentClient()
    runner_mock = ResearchWorkflowRunner(agent_client=client_mock)
    app.dependency_overrides[get_workflow_runner] = lambda: runner_mock
    client = TestClient(app)

    payload = {
        "query": "Evaluate p99 tail latency in distributed Raft consensus algorithms",
        "tenant_id": "tenant-enterprise",
    }
    response = client.post("/api/v1/workflows/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["query"] == payload["query"]
    assert len(data["completed_task_ids"]) >= 1
    assert data["accumulated_evidence_count"] >= 1
    assert data["final_report"] is not None
    assert "sections" in data["final_report"]


def test_api_workflow_short_query_fails():
    settings = Settings()
    app = create_app(settings=settings)
    client = TestClient(app)

    payload = {
        "query": "ab",
    }
    # Pydantic validation rejects min_length < 3
    response = client.post("/api/v1/workflows/execute", json=payload)
    assert response.status_code == 422
