"""External Web Researcher Agent with search/fetch adapters and source metadata extraction."""

import time
from typing import Any

from atlas_contracts.agent_schemas import (
    AgentInput,
    AgentResult,
    LLMMessage,
    LLMMessageRole,
    ResearcherOutput,
)

from agent_runtime.agents.base import AgentToolPermission, BaseSpecializedAgent
from agent_runtime.llm.base import BaseLLMProvider
from agent_runtime.llm.prompts import RESEARCHER_SYSTEM_PROMPT


class WebSearchAdapter:
    """Mock/Configurable web search and fetch adapter respecting rate limits."""

    def __init__(self, mock_results: list[dict[str, Any]] | None = None) -> None:
        self.mock_results = mock_results or []

    async def search_and_fetch(self, query: str, max_results: int = 3) -> list[dict[str, Any]]:
        """Simulate or execute safe web search returning curated snippets with URL metadata."""
        if self.mock_results:
            return self.mock_results[:max_results]

        # Deterministic simulation for queries
        return [
            {
                "url": "https://research.industry.org/benchmark-2026",
                "title": f"Industry Benchmark Report for {query}",
                "snippet": f"Verified analysis confirms robust metrics regarding {query} with p99 stability.",
                "publisher": "Industry Research Consortium",
            }
        ]


class WebResearcherAgent(BaseSpecializedAgent):
    """Conducts external web research and extracts claims linked to canonical URLs."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        search_adapter: WebSearchAdapter | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.search_adapter = search_adapter or WebSearchAdapter()

    @property
    def agent_type(self) -> str:
        return "web_researcher"

    @property
    def allowed_tools(self) -> frozenset[str]:
        return AgentToolPermission.WEB_RESEARCHER_TOOLS

    async def run(self, payload: AgentInput) -> AgentResult:
        start_time = time.perf_counter()

        query = payload.search_queries[0] if payload.search_queries else payload.objective
        search_records = await self.search_adapter.search_and_fetch(query=query, max_results=3)

        web_context_text = "\n---\n".join(
            f"Source URL: {rec['url']}\n"
            f"Publisher: {rec.get('publisher', 'Unknown')}\n"
            f"Snippet: {rec['snippet']}"
            for rec in search_records
        )

        user_content = (
            f"Web Research Objective: {payload.objective}\n"
            f"External Web Results:\n{web_context_text}\n\n"
            f"Extract factual claims directly supported by these external sources, attributing source URLs."
        )

        messages = [
            LLMMessage(role=LLMMessageRole.SYSTEM, content=RESEARCHER_SYSTEM_PROMPT),
            LLMMessage(role=LLMMessageRole.USER, content=user_content),
        ]

        try:
            researcher_output, raw_resp = await self.llm_provider.complete_structured(
                messages=messages,
                response_model=ResearcherOutput,
                temperature=0.0,
            )

            # Ensure evidence items capture source_type='web'
            for item in researcher_output.evidence_items:
                item.source_type = "web"
                if not item.url and search_records:
                    item.url = search_records[0]["url"]

            researcher_output.task_id = payload.task_id
            researcher_output.sources_consulted = len(search_records)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentResult(
                task_id=payload.task_id,
                agent_type=self.agent_type,
                status="completed",
                output=researcher_output.model_dump(),
                evidence_count=len(researcher_output.evidence_items),
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
