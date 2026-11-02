"""Research workflow orchestrator engine executing graph runs and managing threads."""

from typing import Any
from uuid import UUID, uuid4

from langgraph.checkpoint.memory import MemorySaver

from research_orchestrator.workflow.agent_client import AgentRuntimeClient
from research_orchestrator.workflow.graph import build_research_graph
from research_orchestrator.workflow.state import ResearchWorkflowState


class ResearchWorkflowRunner:
    """Manages invocations and thread checkpointing for compiled research workflows."""

    def __init__(
        self,
        agent_client: AgentRuntimeClient | None = None,
        checkpointer: Any | None = None,
    ) -> None:
        self.agent_client = agent_client or AgentRuntimeClient()
        self.checkpointer = checkpointer or MemorySaver()
        self.graph = build_research_graph(
            agent_client=self.agent_client,
            checkpointer=self.checkpointer,
        )

    async def execute_run(
        self,
        query: str,
        research_id: UUID | None = None,
        tenant_id: str = "default",
        max_retries: int = 1,
        thread_id: str | None = None,
    ) -> ResearchWorkflowState:
        """Run workflow from start to completion or resume from existing thread checkpoint."""
        rid = str(research_id or uuid4())
        tid = thread_id or f"thread_{rid}"

        initial_state: ResearchWorkflowState = {
            "research_id": rid,
            "tenant_id": tenant_id,
            "query": query,
            "max_retries": max_retries,
            "retry_count": 0,
            "thread_id": tid,
            "status": "queued",
            "iteration": 0,
            "planned_subtasks": [],
            "completed_task_ids": [],
            "accumulated_evidence": [],
            "verified_evidence": [],
            "unverified_claims": [],
            "critic_gaps": [],
            "contradictions": [],
            "final_report": None,
            "error": None,
        }

        config = {"configurable": {"thread_id": tid}}
        final_state = await self.graph.ainvoke(initial_state, config=config)
        return final_state
