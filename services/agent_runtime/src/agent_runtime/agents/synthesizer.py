"""Research Synthesizer Agent composing final reports strictly grounded in verified evidence."""

import time

from atlas_contracts.agent_schemas import (
    AgentInput,
    AgentResult,
    LLMMessage,
    LLMMessageRole,
    SynthesizerOutput,
)

from agent_runtime.agents.base import AgentToolPermission, BaseSpecializedAgent
from agent_runtime.llm.base import BaseLLMProvider
from agent_runtime.llm.prompts import SYNTHESIZER_SYSTEM_PROMPT


class SynthesizerAgent(BaseSpecializedAgent):
    """Generates structured, grounded research reports binding each statement to verified evidence IDs."""

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm_provider = llm_provider

    @property
    def agent_type(self) -> str:
        return "synthesizer"

    @property
    def allowed_tools(self) -> frozenset[str]:
        return AgentToolPermission.SYNTHESIZER_TOOLS

    async def run(self, payload: AgentInput) -> AgentResult:
        start_time = time.perf_counter()

        verified_evidence = payload.context_data.get("verified_evidence", [])
        evidence_text = (
            "\n---\n".join(
                f"Evidence ID: {item.get('evidence_id')}\n"
                f"Claim: {item.get('claim')}\n"
                f"Passage: {item.get('source_passage')}\n"
                f"Source Type: {item.get('source_type')}"
                for item in verified_evidence
            )
            or "No verified evidence available."
        )

        user_content = (
            f"Research Question: {payload.objective}\n"
            f"Verified Evidence Records:\n{evidence_text}\n\n"
            f"Compose a comprehensive research report using ONLY the verified evidence provided. "
            f"Include inline citation tags like [ev_xxx] for every factual statement."
        )

        messages = [
            LLMMessage(role=LLMMessageRole.SYSTEM, content=SYNTHESIZER_SYSTEM_PROMPT),
            LLMMessage(role=LLMMessageRole.USER, content=user_content),
        ]

        try:
            synth_output, raw_resp = await self.llm_provider.complete_structured(
                messages=messages,
                response_model=SynthesizerOutput,
                temperature=0.0,
            )

            # Count total citations cited
            total_cites = sum(len(s.cited_evidence_ids) for s in synth_output.sections)
            synth_output.total_citations = total_cites

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentResult(
                task_id=payload.task_id,
                agent_type=self.agent_type,
                status="completed",
                output=synth_output.model_dump(),
                evidence_count=total_cites,
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
