"""Agent dispatch and execution REST API endpoints."""

from typing import Annotated

from agent_runtime.agents.registry import AgentRegistry
from agent_runtime.core.config import Settings, get_settings
from agent_runtime.llm.factory import get_resilient_llm_service
from atlas_contracts.agent_schemas import AgentInput, AgentResult
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])

_registry_instance: AgentRegistry | None = None


def get_agent_registry(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AgentRegistry:
    global _registry_instance
    if _registry_instance is None:
        llm_service = get_resilient_llm_service(settings)
        # Point to retrieval service if configured
        retrieval_url = f"http://{settings.host}:8003"
        _registry_instance = AgentRegistry(
            llm_provider=llm_service.primary_provider,
            retrieval_service_url=retrieval_url,
        )
    return _registry_instance


@router.get(
    "/roles",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List registered specialized agent roles",
)
async def list_agent_roles(
    registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
) -> list[str]:
    return registry.list_available_agents()


@router.post(
    "/dispatch",
    response_model=AgentResult,
    status_code=status.HTTP_200_OK,
    summary="Dispatch a structured research task to a specialized agent",
)
async def dispatch_agent_task(
    payload: AgentInput,
    registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
) -> AgentResult:
    try:
        agent = registry.get_agent(payload.agent_type)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result = await agent.run(payload)
    if result.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent '{payload.agent_type}' execution failed: {result.error_message}",
        )

    return result
