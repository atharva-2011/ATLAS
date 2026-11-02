"""Tests for atlas_contracts shared models."""

from datetime import datetime

from atlas_contracts import ErrorResponse, HealthResponse, ReadinessResponse, ServiceStatus


def test_health_response_defaults():
    resp = HealthResponse(service="api-gateway", version="0.1.0")
    assert resp.status == ServiceStatus.OK.value
    assert resp.service == "api-gateway"
    assert resp.version == "0.1.0"
    assert isinstance(resp.timestamp, datetime)
    assert resp.timestamp.tzinfo is not None

    data = resp.model_dump()
    assert data["status"] == "ok"
    assert data["service"] == "api-gateway"


def test_readiness_response_with_checks():
    resp = ReadinessResponse(
        service="ingestion-service", version="0.1.0", checks={"config": "ok", "storage": "ready"}
    )
    assert resp.status == ServiceStatus.READY.value
    assert resp.checks["config"] == "ok"
    assert resp.checks["storage"] == "ready"


def test_error_response_serialization():
    resp = ErrorResponse(
        error="INVALID_REQUEST",
        message="Request payload was malformed",
        correlation_id="corr-12345",
        details={"field": "query"},
    )
    data = resp.model_dump()
    assert data["error"] == "INVALID_REQUEST"
    assert data["correlation_id"] == "corr-12345"
    assert data["details"] == {"field": "query"}
