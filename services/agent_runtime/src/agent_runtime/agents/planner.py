"""Planner Agent implementation decomposing research questions into executable subtasks."""

import time

from atlas_contracts.agent_schemas import (
    AgentInput,
    AgentResult,
    LLMMessage,
    LLMMessageRole,
    PlannerOutput,
)

from agent_runtime.agents.base import AgentToolPermission, BaseSpecializedAgent
from agent_runtime.llm.base import BaseLLMProvider
from agent_runtime.llm.prompts import PLANNER_SYSTEM_PROMPT


class PlannerAgent(BaseSpecializedAgent):
    """Decomposes complex research queries into structured subtasks with dependencies and scope."""

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm_provider = llm_provider

    @property
    def agent_type(self) -> str:
        return "planner"

    @property
    def allowed_tools(self) -> frozenset[str]:
        return AgentToolPermission.PLANNER_TOOLS

    async def run(self, payload: AgentInput) -> AgentResult:
        start_time = time.perf_counter()

        user_content = (
            f"Research Query: {payload.objective}\n"
            f"Context / Parameters: {payload.context_data}\n"
            f"Please decompose into independent and dependent subtasks for internal document and external research."
        )

        messages = [
            LLMMessage(role=LLMMessageRole.SYSTEM, content=PLANNER_SYSTEM_PROMPT),
            LLMMessage(role=LLMMessageRole.USER, content=user_content),
        ]

        try:
            planner_output, raw_resp = await self.llm_provider.complete_structured(
                messages=messages,
                response_model=PlannerOutput,
                temperature=0.0,
            )

            # Ensure query in output matches input
            if not planner_output.query or planner_output.query == "Target Query":
                planner_output.query = payload.objective

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentResult(
                task_id=payload.task_id,
                agent_type=self.agent_type,
                status="completed",
                output=planner_output.model_dump(),
                evidence_count=0,
                usage=raw_resp.usage,
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentResult(
                task_id=payload.task_id,
                agent_type=self.agent_type,
                status="failed",
                error_message=str(exc),
                execution_time_ms=elapsed_ms,
            )
