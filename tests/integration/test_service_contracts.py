"""Integration tests verifying all six services satisfy shared health and readiness contracts."""

import pytest
from agent_runtime.main import create_app as create_agent_runtime
from api_gateway.main import create_app as create_api_gateway
from atlas_contracts import HealthResponse, ReadinessResponse
from evaluation_service.main import create_app as create_evaluation_service
from fastapi.testclient import TestClient
from ingestion_service.main import create_app as create_ingestion_service
from research_orchestrator.main import create_app as create_research_orchestrator
from retrieval_service.main import create_app as create_retrieval_service

SERVICES = [
    ("api-gateway", create_api_gateway),
    ("research-orchestrator", create_research_orchestrator),
    ("ingestion-service", create_ingestion_service),
    ("retrieval-service", create_retrieval_service),
    ("agent-runtime", create_agent_runtime),
    ("evaluation-service", create_evaluation_service),
]


@pytest.mark.parametrize("expected_service_name,app_factory", SERVICES)
def test_all_services_liveness_contract(expected_service_name: str, app_factory):
    app = app_factory()
    client = TestClient(app)

    response = client.get("/health/live")
    assert response.status_code == 200

    # Validate against strict Pydantic contract
    parsed = HealthResponse.model_validate(response.json())
    assert parsed.status == "ok"
    assert parsed.service == expected_service_name
    assert parsed.version == "0.1.0"
    assert parsed.timestamp is not None


@pytest.mark.parametrize("expected_service_name,app_factory", SERVICES)
def test_all_services_readiness_contract(expected_service_name: str, app_factory):
    app = app_factory()
    client = TestClient(app)

    response = client.get("/health/ready")
    assert response.status_code == 200

    # Validate against strict Pydantic contract
    parsed = ReadinessResponse.model_validate(response.json())
    assert parsed.status == "ready"
    assert parsed.service == expected_service_name
    assert parsed.version == "0.1.0"
    assert "configuration" in parsed.checks
