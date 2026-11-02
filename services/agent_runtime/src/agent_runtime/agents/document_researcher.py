"""Document Researcher Agent using Hybrid Retrieval Service to produce structured evidence."""

import time
from typing import Any
from uuid import UUID

import httpx
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


class DocumentResearcherAgent(BaseSpecializedAgent):
    """Executes targeted hybrid retrieval queries over internal documents and extracts evidence."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        retrieval_service_url: str = "http://127.0.0.1:8003",
        mock_retrieval_response: list[dict[str, Any]] | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.retrieval_service_url = retrieval_service_url.rstrip("/")
        self.mock_retrieval_response = mock_retrieval_response

    @property
    def agent_type(self) -> str:
        return "document_researcher"

    @property
    def allowed_tools(self) -> frozenset[str]:
        return AgentToolPermission.DOCUMENT_RESEARCHER_TOOLS

    async def _fetch_hybrid_passages(
        self,
        tenant_id: str,
        query: str,
        document_id: UUID | None = None,
        top_k: int = 4,
    ) -> list[dict[str, Any]]:
        """Query Retrieval Service hybrid endpoint or use provided mock fixtures."""
        if self.mock_retrieval_response is not None:
            return self.mock_retrieval_response

        url = f"{self.retrieval_service_url}/api/v1/retrieval/hybrid-search"
        payload = {
            "tenant_id": tenant_id,
            "query": query,
            "top_k": top_k,
            "document_id": str(document_id) if document_id else None,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("results", [])
        except Exception:
            # Fall back to empty candidate list if service unavailable
            pass
        return []

    async def run(self, payload: AgentInput) -> AgentResult:
        start_time = time.perf_counter()

        # Step 1: Perform retrieval across suggested queries or task objective
        search_query = payload.search_queries[0] if payload.search_queries else payload.objective
        doc_id = payload.document_ids[0] if payload.document_ids else None

        retrieved_items = await self._fetch_hybrid_passages(
            tenant_id=payload.tenant_id,
            query=search_query,
            document_id=doc_id,
            top_k=4,
        )

        # Step 2: Build LLM prompt with retrieved context
        passages_text = (
            "\n---\n".join(
                f"Passage ID: {item.get('chunk_id', 'chunk_0')}\n"
                f"Text: {item.get('text', '')}\n"
                f"Locator: {item.get('locator', {})}"
                for item in retrieved_items
            )
            or "No relevant passages found."
        )

        user_content = (
            f"Task Objective: {payload.objective}\n"
            f"Retrieved Passages from Internal Documents:\n{passages_text}\n\n"
            f"Extract all factual claims directly supported by these passages."
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

            # Ensure task ID aligns
            researcher_output.task_id = payload.task_id
            researcher_output.sources_consulted = len(retrieved_items)

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
