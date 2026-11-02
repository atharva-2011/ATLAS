"""HTTP client adapter communicating with Agent Runtime microservice over REST."""

import httpx
from atlas_contracts.agent_schemas import AgentInput, AgentResult


class AgentRuntimeClient:
    """Client for dispatching specialized tasks to the Agent Runtime service."""

    def __init__(self, base_url: str = "http://127.0.0.1:8004") -> None:
        self.base_url = base_url.rstrip("/")

    async def list_roles(self) -> list[str]:
        """Query agent runtime for registered agent roles."""
        url = f"{self.base_url}/api/v1/agents/roles"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                return res.json()
        return [
            "planner",
            "document_researcher",
            "web_researcher",
            "evidence_verifier",
            "critic",
            "synthesizer",
        ]

    async def dispatch(self, payload: AgentInput) -> AgentResult:
        """Post structured AgentInput to /api/v1/agents/dispatch."""
        url = f"{self.base_url}/api/v1/agents/dispatch"
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(url, json=payload.model_dump())
            if res.status_code == 200:
                return AgentResult.model_validate(res.json())
            return AgentResult(
                task_id=payload.task_id,
                agent_type=payload.agent_type,
                status="failed",
                error_message=f"Agent runtime returned {res.status_code}: {res.text}",
            )
