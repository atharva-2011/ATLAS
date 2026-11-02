"""Mock LLM provider for deterministic, fast, offline unit and integration tests."""

import asyncio
import time
from typing import TypeVar

from atlas_contracts.agent_schemas import (
    ClaimVerificationVerdict,
    CriticOutput,
    ExtractedEvidenceItem,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    PlannedSubtask,
    PlannerOutput,
    ReportSection,
    ResearcherOutput,
    SynthesizerOutput,
    VerifiedClaim,
    VerifierOutput,
)
from pydantic import BaseModel

from agent_runtime.llm.base import BaseLLMProvider, LLMTimeoutError
from agent_runtime.llm.parser import parse_structured_output

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(BaseLLMProvider):
    """Deterministic local mock provider generating conforming structured outputs for all agent roles."""

    def __init__(
        self,
        model_name: str = "atlas-mock-v1",
        simulate_latency_seconds: float = 0.0,
        should_timeout: bool = False,
        custom_responses: list[str] | None = None,
    ) -> None:
        self._model_name = model_name
        self.simulate_latency_seconds = simulate_latency_seconds
        self.should_timeout = should_timeout
        self.custom_responses = custom_responses or []
        self._call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _generate_default_model(self, response_model: type[T]) -> T:
        """Create a valid default instance matching the requested schema."""
        if response_model == PlannerOutput:
            return PlannerOutput(
                query="Target Query",
                plan_summary="Systematic research plan across primary and secondary sources.",
                scope_dimensions=["technology", "market", "validation"],
                subtasks=[
                    PlannedSubtask(
                        task_id="task_1",
                        objective="Investigate architectural requirements and hardware bounds.",
                        agent_type="document_researcher",
                        search_queries=["architecture requirements", "system bounds"],
                        success_criteria="Identified concrete hardware limits.",
                    ),
                    PlannedSubtask(
                        task_id="task_2",
                        objective="Verify market readiness and competitive benchmarks.",
                        agent_type="web_researcher",
                        dependencies=["task_1"],
                        search_queries=["market readiness benchmark"],
                        success_criteria="Obtained competitive analysis metrics.",
                    ),
                ],
                estimated_depth="medium",
            )  # type: ignore

        if response_model == ResearcherOutput:
            return ResearcherOutput(
                task_id="task_mock",
                summary_findings="Core findings confirm consistent performance across tested boundaries.",
                evidence_items=[
                    ExtractedEvidenceItem(
                        evidence_id="ev_mock_1",
                        claim="System latency is bounded under 50ms at 95th percentile.",
                        source_passage="Empirical tests demonstrated p95 response times remaining strictly below 50ms.",
                        source_type="internal_document",
                        confidence=0.96,
                    )
                ],
                unresolved_questions=[],
                sources_consulted=1,
            )  # type: ignore

        if response_model == VerifierOutput:
            return VerifierOutput(
                total_claims=1,
                verified_claims=[
                    VerifiedClaim(
                        claim="System latency is bounded under 50ms at 95th percentile.",
                        evidence_id="ev_mock_1",
                        verdict=ClaimVerificationVerdict.SUPPORTED,
                        rationale="Source explicitly states p95 response time strictly below 50ms.",
                        confidence=0.98,
                    )
                ],
                overall_support_ratio=1.0,
                has_contradictions=False,
            )  # type: ignore

        if response_model == CriticOutput:
            return CriticOutput(
                coverage_score=0.92,
                is_sufficient=True,
                contradictions_found=[],
                gaps=[],
                recommendation="proceed",
            )  # type: ignore

        if response_model == SynthesizerOutput:
            return SynthesizerOutput(
                title="Consolidated Research Intelligence Report",
                executive_summary="Executive findings validate architectural bounds and latency constraints.",
                sections=[
                    ReportSection(
                        title="1. Performance & Latency",
                        content="Empirical validation demonstrates sub-50ms latency at p95 [ev_mock_1].",
                        cited_evidence_ids=["ev_mock_1"],
                    )
                ],
                limitations=["Analysis bounded by available internal benchmarks."],
                full_markdown="# Consolidated Research Intelligence Report\n\nExecutive findings validate architectural bounds.",
                total_citations=1,
            )  # type: ignore

        # Fallback for arbitrary model if constructible with defaults
        return response_model()

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        self._call_count += 1
        start_time = time.perf_counter()

        if self.should_timeout:
            await asyncio.sleep(timeout or 0.1)
            raise LLMTimeoutError(
                f"Mock LLM timed out after {timeout}s",
                provider=self.provider_name,
            )

        if self.simulate_latency_seconds > 0:
            await asyncio.sleep(self.simulate_latency_seconds)

        if self.custom_responses:
            content = self.custom_responses.pop(0)
        else:
            last_msg = messages[-1].content if messages else ""
            content = f"Mock completion for: {last_msg[:50]}"

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return LLMResponse(
            content=content,
            model=self._model_name,
            provider=self.provider_name,
            usage=LLMUsage(
                prompt_tokens=sum(len(m.content.split()) for m in messages),
                completion_tokens=len(content.split()),
                total_tokens=sum(len(m.content.split()) for m in messages) + len(content.split()),
                estimated_cost_usd=0.0,
            ),
            latency_ms=latency_ms,
        )

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> tuple[T, LLMResponse]:
        if self.custom_responses:
            raw_response = await self.complete(messages, temperature, max_tokens, timeout)
            parsed = parse_structured_output(raw_response.content, response_model)
            raw_response.parsed = parsed.model_dump()
            return parsed, raw_response

        # Use default conforming model
        instance = self._generate_default_model(response_model)
        content_json = instance.model_dump_json(indent=2)
        raw_response = await self.complete(messages, temperature, max_tokens, timeout)
        raw_response.content = content_json
        raw_response.parsed = instance.model_dump()

        return instance, raw_response
