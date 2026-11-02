"""Workflow nodes wrapping specialized research agents and state updates."""

import asyncio
from typing import Any

from atlas_contracts.agent_schemas import AgentInput

from research_orchestrator.workflow.agent_client import AgentRuntimeClient
from research_orchestrator.workflow.state import ResearchWorkflowState


class WorkflowNodeHandler:
    """Encapsulates node execution logic connecting LangGraph states to specialized agents via HTTP."""

    def __init__(self, agent_client: AgentRuntimeClient) -> None:
        self.agent_client = agent_client

    async def intake_node(self, state: ResearchWorkflowState) -> dict[str, Any]:
        """Validate input question and initialize state for planning."""
        query = state.get("query", "").strip()
        if len(query) < 3:
            return {
                "status": "failed",
                "error": "Query too short to execute meaningful research investigation.",
            }
        return {
            "status": "planning",
            "iteration": state.get("iteration", 0) + 1,
        }

    async def planning_node(self, state: ResearchWorkflowState) -> dict[str, Any]:
        """Invoke Planner Agent to decompose query into directed subtasks."""
        payload = AgentInput(
            task_id="plan_init",
            objective=state["query"],
            agent_type="planner",
            tenant_id=state.get("tenant_id", "default"),
        )

        res = await self.agent_client.dispatch(payload)
        if res.status != "completed" or not res.output:
            return {
                "status": "failed",
                "error": f"Planning failed: {res.error_message or 'No output generated'}",
            }

        subtasks = res.output.get("subtasks", [])
        return {
            "status": "researching",
            "planned_subtasks": subtasks,
        }

    async def execute_task_worker(
        self,
        subtask: dict[str, Any],
        state: ResearchWorkflowState,
    ) -> dict[str, Any]:
        """Execute an individual subtask worker (document or web researcher)."""
        task_id = subtask.get("task_id", "task_0")
        agent_type = subtask.get("agent_type", "document_researcher")

        payload = AgentInput(
            task_id=task_id,
            objective=subtask.get("objective", state["query"]),
            agent_type=agent_type,
            tenant_id=state.get("tenant_id", "default"),
            search_queries=subtask.get("search_queries", []),
        )

        res = await self.agent_client.dispatch(payload)
        new_evidence: list[dict[str, Any]] = []
        if res.status == "completed" and res.output:
            new_evidence = res.output.get("evidence_items", [])

        return {
            "completed_task_ids": [task_id],
            "accumulated_evidence": new_evidence,
        }

    async def parallel_research_node(self, state: ResearchWorkflowState) -> dict[str, Any]:
        """Fan-out execution of planned research subtasks with bounded parallelism."""
        subtasks = state.get("planned_subtasks", [])
        if not subtasks:
            # Fallback single task
            subtasks = [
                {
                    "task_id": "task_default",
                    "agent_type": "document_researcher",
                    "objective": state["query"],
                }
            ]

        # Execute workers concurrently
        tasks = [self.execute_task_worker(st, state) for st in subtasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_completed: list[str] = []
        all_evidence: list[dict[str, Any]] = []

        for r in results:
            if isinstance(r, dict):
                all_completed.extend(r.get("completed_task_ids", []))
                all_evidence.extend(r.get("accumulated_evidence", []))

        return {
            "status": "verifying",
            "completed_task_ids": all_completed,
            "accumulated_evidence": all_evidence,
        }

    async def verification_node(self, state: ResearchWorkflowState) -> dict[str, Any]:
        """Verify collected evidence items with the Evidence Verifier agent."""
        evidence_items = state.get("accumulated_evidence", [])

        payload = AgentInput(
            task_id="verify_batch",
            objective="Verify grounding of extracted claims",
            agent_type="evidence_verifier",
            context_data={"evidence_items": evidence_items},
        )

        res = await self.agent_client.dispatch(payload)
        verified: list[dict[str, Any]] = []
        contradictions: list[str] = []

        if res.status == "completed" and res.output:
            for item in res.output.get("verified_claims", []):
                if item.get("verdict") in ("supported", "partially_supported"):
                    verified.append(item)
                elif item.get("verdict") == "contradicted":
                    contradictions.append(item.get("claim", ""))

        # If empty or verifier returned none, preserve supported evidence records
        if not verified and evidence_items:
            verified = evidence_items

        return {
            "status": "critiquing",
            "verified_evidence": verified,
            "contradictions": contradictions,
        }

    async def critic_node(self, state: ResearchWorkflowState) -> dict[str, Any]:
        """Audit coverage and identify gaps before synthesis."""
        payload = AgentInput(
            task_id="critic_audit",
            objective=state["query"],
            agent_type="critic",
            context_data={
                "subtasks": state.get("planned_subtasks", []),
                "evidence_items": state.get("accumulated_evidence", []),
            },
        )

        res = await self.agent_client.dispatch(payload)
        gaps: list[dict[str, Any]] = []
        recommendation = "proceed"

        if res.status == "completed" and res.output:
            gaps = res.output.get("gaps", [])
            recommendation = res.output.get("recommendation", "proceed")

        return {
            "status": "synthesizing" if recommendation == "proceed" else "evaluating_retry",
            "critic_gaps": gaps,
        }

    async def synthesis_node(self, state: ResearchWorkflowState) -> dict[str, Any]:
        """Synthesize final report grounded in verified evidence."""
        verified = state.get("verified_evidence", []) or state.get("accumulated_evidence", [])

        payload = AgentInput(
            task_id="synth_report",
            objective=state["query"],
            agent_type="synthesizer",
            context_data={"verified_evidence": verified},
        )

        res = await self.agent_client.dispatch(payload)
        if res.status != "completed" or not res.output:
            return {
                "status": "failed",
                "error": f"Synthesis failed: {res.error_message or 'Unknown error'}",
            }

        return {
            "status": "completed",
            "final_report": res.output,
        }
