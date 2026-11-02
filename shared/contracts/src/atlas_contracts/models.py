"""Shared DTOs and API boundary models for ATLAS microservices."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


class ServiceStatus(StrEnum):
    """Standardized service health status strings."""

    OK = "ok"
    READY = "ready"
    DEGRADED = "degraded"
    ERROR = "error"


class HealthResponse(BaseModel):
    """Payload returned by /health/live endpoints."""

    status: str = Field(
        default=ServiceStatus.OK.value, description="Status of the process event loop"
    )
    service: str = Field(description="Unique service identifier")
    version: str = Field(description="Service semantic version")
    timestamp: datetime = Field(
        default_factory=get_utc_now, description="UTC timestamp of the check"
    )


class ReadinessResponse(BaseModel):
    """Payload returned by /health/ready endpoints."""

    status: str = Field(
        default=ServiceStatus.READY.value, description="Readiness status to receive traffic"
    )
    service: str = Field(description="Unique service identifier")
    version: str = Field(description="Service semantic version")
    timestamp: datetime = Field(
        default_factory=get_utc_now, description="UTC timestamp of the check"
    )
    checks: dict[str, str] = Field(default_factory=dict, description="Component readiness checks")


class ErrorResponse(BaseModel):
    """Standardized error envelope across all ATLAS services."""

    error: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable description")
    correlation_id: str | None = Field(default=None, description="Request correlation identifier")
    timestamp: datetime = Field(
        default_factory=get_utc_now, description="UTC timestamp of the error"
    )
    details: dict[str, Any] | None = Field(default=None, description="Optional diagnostic details")
