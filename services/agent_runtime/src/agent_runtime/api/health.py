"""Health and readiness check endpoints for Agent Runtime."""

from agent_runtime.core.config import Settings, get_settings
from atlas_contracts import HealthResponse, ReadinessResponse
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", response_model=HealthResponse)
async def liveness(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Liveness probe indicating the service process and event loop are running."""
    return HealthResponse(
        service=settings.service_name,
        version=settings.service_version,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(settings: Settings = Depends(get_settings)) -> ReadinessResponse:
    """Readiness probe indicating the service has booted and can accept traffic."""
    return ReadinessResponse(
        service=settings.service_name,
        version=settings.service_version,
        checks={"configuration": "ready"},
    )
