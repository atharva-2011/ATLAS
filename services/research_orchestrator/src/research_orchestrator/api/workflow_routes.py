"""API endpoints for initiating and querying LangGraph multi-agent research runs."""

from typing import Annotated, Any

from atlas_contracts.domain import ResearchCreate
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from research_orchestrator.core.config import Settings, get_settings
from research_orchestrator.workflow.agent_client import AgentRuntimeClient
from research_orchestrator.workflow.runner import ResearchWorkflowRunner

router = APIRouter(prefix="/api/v1/workflows", tags=["Research Workflows"])

_runner_instance: ResearchWorkflowRunner | None = None


def get_workflow_runner(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResearchWorkflowRunner:
    global _runner_instance
    if _runner_instance is None:
        client = AgentRuntimeClient(base_url="http://127.0.0.1:8004")
        _runner_instance = ResearchWorkflowRunner(agent_client=client)
    return _runner_instance


class WorkflowRunResponse(BaseModel):
    research_id: str
    status: str
    query: str
    completed_task_ids: list[str] = Field(default_factory=list)
    accumulated_evidence_count: int = 0
    final_report: dict[str, Any] | None = None
    error: str | None = None


@router.post(
    "/execute",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute end-to-end multi-agent research workflow",
)
async def execute_research_workflow(
    payload: ResearchCreate,
    runner: Annotated[ResearchWorkflowRunner, Depends(get_workflow_runner)],
) -> WorkflowRunResponse:
    try:
        final_state = await runner.execute_run(
            query=payload.query,
            tenant_id=payload.tenant_id,
        )
        return WorkflowRunResponse(
            research_id=final_state["research_id"],
            status=final_state["status"],
            query=final_state["query"],
            completed_task_ids=final_state.get("completed_task_ids", []),
            accumulated_evidence_count=len(final_state.get("accumulated_evidence", [])),
            final_report=final_state.get("final_report"),
            error=final_state.get("error"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {exc}",
        ) from exc
