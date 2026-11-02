"""Compiled LangGraph Research Supervisor workflow with checkpoint persistence and conditional retries."""

from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from research_orchestrator.workflow.agent_client import AgentRuntimeClient
from research_orchestrator.workflow.nodes import WorkflowNodeHandler
from research_orchestrator.workflow.state import ResearchWorkflowState


def should_continue_after_intake(state: ResearchWorkflowState) -> Literal["planning", "failed"]:
    if state.get("status") == "failed" or state.get("error"):
        return "failed"
    return "planning"


def should_continue_after_planning(
    state: ResearchWorkflowState,
) -> Literal["parallel_research", "failed"]:
    if state.get("status") == "failed" or not state.get("planned_subtasks"):
        return "failed"
    return "parallel_research"


def should_retry_or_synthesize(
    state: ResearchWorkflowState,
) -> Literal["parallel_research", "synthesis"]:
    """Conditional edge checking whether to retry targeted research or proceed to synthesis."""
    status = state.get("status", "")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 1)
    gaps = state.get("critic_gaps", [])

    if status == "evaluating_retry" and gaps and retry_count < max_retries:
        # Bounded retry: loop back for additional evidence
        state["retry_count"] = retry_count + 1
        return "parallel_research"

    return "synthesis"


def build_research_graph(
    agent_client: AgentRuntimeClient,
    checkpointer: Any | None = None,
) -> Any:
    """Build and compile the multi-agent research StateGraph."""
    handler = WorkflowNodeHandler(agent_client)
    workflow = StateGraph(ResearchWorkflowState)

    # Add Nodes
    workflow.add_node("intake", handler.intake_node)
    workflow.add_node("planning", handler.planning_node)
    workflow.add_node("parallel_research", handler.parallel_research_node)
    workflow.add_node("verification", handler.verification_node)
    workflow.add_node("critic", handler.critic_node)
    workflow.add_node("synthesis", handler.synthesis_node)

    # Connect Edges
    workflow.add_edge(START, "intake")

    workflow.add_conditional_edges(
        "intake",
        should_continue_after_intake,
        {
            "planning": "planning",
            "failed": END,
        },
    )

    workflow.add_conditional_edges(
        "planning",
        should_continue_after_planning,
        {
            "parallel_research": "parallel_research",
            "failed": END,
        },
    )

    workflow.add_edge("parallel_research", "verification")
    workflow.add_edge("verification", "critic")

    workflow.add_conditional_edges(
        "critic",
        should_retry_or_synthesize,
        {
            "parallel_research": "parallel_research",
            "synthesis": "synthesis",
        },
    )

    workflow.add_edge("synthesis", END)

    # In-memory checkpointer by default if none provided
    saver = checkpointer or MemorySaver()
    return workflow.compile(checkpointer=saver)
