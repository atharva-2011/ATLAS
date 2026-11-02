"""Typed LangGraph ResearchState with operator reducers for safe parallel accumulation."""

import operator
from typing import Annotated, Any

from typing_extensions import TypedDict


class ResearchWorkflowState(TypedDict):
    """LangGraph state representation for end-to-end multi-agent research runs."""

    # Run Identifiers & Config
    research_id: str
    tenant_id: str
    query: str
    max_retries: int
    retry_count: int
    thread_id: str

    # Workflow Status & State Tracking
    status: (
        str  # planning | researching | verifying | critiquing | synthesizing | completed | failed
    )
    iteration: int

    # Parallel Reducer Collections (appends from concurrent task nodes)
    planned_subtasks: list[dict[str, Any]]
    completed_task_ids: Annotated[list[str], operator.add]
    accumulated_evidence: Annotated[list[dict[str, Any]], operator.add]
    verified_evidence: list[dict[str, Any]]
    unverified_claims: list[dict[str, Any]]
    critic_gaps: list[dict[str, Any]]
    contradictions: list[str]

    # Final Output Report
    final_report: dict[str, Any] | None
    error: str | None
