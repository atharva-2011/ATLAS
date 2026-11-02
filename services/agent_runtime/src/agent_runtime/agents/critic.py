"""Critic Agent assessing coverage completeness, blindspots, and research gaps."""

import time

from atlas_contracts.agent_schemas import (
    AgentInput,
    AgentResult,
    CriticOutput,
    LLMMessage,
    LLMMessageRole,
)

from agent_runtime.agents.base import AgentToolPermission, BaseSpecializedAgent
from agent_runtime.llm.base import BaseLLMProvider
from agent_runtime.llm.prompts import CRITIC_SYSTEM_PROMPT


class CriticAgent(BaseSpecializedAgent):
    """Quality review agent auditing research coverage and identifying unaddressed gaps."""

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm_provider = llm_provider

    @property
    def agent_type(self) -> str:
        return "critic"

    @property
    def allowed_tools(self) -> frozenset[str]:
        return AgentToolPermission.CRITIC_TOOLS

    async def run(self, payload: AgentInput) -> AgentResult:
        start_time = time.perf_counter()

        planned_subtasks = payload.context_data.get("subtasks", [])
        evidence_items = payload.context_data.get("evidence_items", [])

        user_content = (
            f"Overall Objective: {payload.objective}\n"
            f"Planned Subtasks: {planned_subtasks}\n"
            f"Accumulated Evidence Records: {len(evidence_items)} items collected.\n"
            f"Audit coverage, identify contradictions, and determine if research is sufficient to proceed to synthesis."
        )

        messages = [
            LLMMessage(role=LLMMessageRole.SYSTEM, content=CRITIC_SYSTEM_PROMPT),
            LLMMessage(role=LLMMessageRole.USER, content=user_content),
        ]

        try:
            critic_output, raw_resp = await self.llm_provider.complete_structured(
                messages=messages,
                response_model=CriticOutput,
                temperature=0.0,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentResult(
                task_id=payload.task_id,
                agent_type=self.agent_type,
                status="completed",
                output=critic_output.model_dump(),
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
