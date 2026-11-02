"""Evidence Verifier Agent strictly validating claims against referenced source passages."""

import time
from typing import Any

from atlas_contracts.agent_schemas import (
    AgentInput,
    AgentResult,
    LLMMessage,
    LLMMessageRole,
    VerifierOutput,
)

from agent_runtime.agents.base import AgentToolPermission, BaseSpecializedAgent
from agent_runtime.llm.base import BaseLLMProvider
from agent_runtime.llm.prompts import VERIFIER_SYSTEM_PROMPT


class EvidenceVerifierAgent(BaseSpecializedAgent):
    """Independent verification agent that checks claim-to-source support and detects contradictions."""

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm_provider = llm_provider

    @property
    def agent_type(self) -> str:
        return "evidence_verifier"

    @property
    def allowed_tools(self) -> frozenset[str]:
        return AgentToolPermission.VERIFIER_TOOLS

    async def verify_evidence_items(
        self,
        evidence_items: list[dict[str, Any]],
    ) -> VerifierOutput:
        """Verify an arbitrary batch of extracted evidence records."""
        if not evidence_items:
            return VerifierOutput(
                total_claims=0,
                verified_claims=[],
                overall_support_ratio=1.0,
                has_contradictions=False,
            )

        pairs_text = "\n---\n".join(
            f"Evidence ID: {item.get('evidence_id', f'ev_{idx}')}\n"
            f"Claim: {item.get('claim', '')}\n"
            f"Referenced Source Passage: {item.get('source_passage', '')}"
            for idx, item in enumerate(evidence_items)
        )

        user_content = (
            f"Please verify each of the following claims against its corresponding source passage.\n\n"
            f"{pairs_text}"
        )

        messages = [
            LLMMessage(role=LLMMessageRole.SYSTEM, content=VERIFIER_SYSTEM_PROMPT),
            LLMMessage(role=LLMMessageRole.USER, content=user_content),
        ]

        output, _ = await self.llm_provider.complete_structured(
            messages=messages,
            response_model=VerifierOutput,
            temperature=0.0,
        )
        return output

    async def run(self, payload: AgentInput) -> AgentResult:
        start_time = time.perf_counter()

        evidence_items = payload.context_data.get("evidence_items", [])
        try:
            verifier_output = await self.verify_evidence_items(evidence_items)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return AgentResult(
                task_id=payload.task_id,
                agent_type=self.agent_type,
                status="completed",
                output=verifier_output.model_dump(),
                evidence_count=verifier_output.total_claims,
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
