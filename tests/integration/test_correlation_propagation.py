"""Integration tests verifying correlation ID generation and propagation across all six services."""

import re

import pytest
from agent_runtime.main import create_app as create_agent_runtime
from api_gateway.main import create_app as create_api_gateway
from atlas_observability import CORRELATION_ID_HEADER
from evaluation_service.main import create_app as create_evaluation_service
from fastapi.testclient import TestClient
from ingestion_service.main import create_app as create_ingestion_service
from research_orchestrator.main import create_app as create_research_orchestrator
from retrieval_service.main import create_app as create_retrieval_service

SERVICES = [
    create_api_gateway,
    create_research_orchestrator,
    create_ingestion_service,
    create_retrieval_service,
    create_agent_runtime,
    create_evaluation_service,
]


@pytest.mark.parametrize("app_factory", SERVICES)
def test_generates_correlation_id_when_absent(app_factory):
    app = app_factory()
    client = TestClient(app)

    response = client.get("/health/live")
    assert response.status_code == 200
    assert CORRELATION_ID_HEADER in response.headers
    corr_id = response.headers[CORRELATION_ID_HEADER]
    # UUID pattern
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", corr_id)


@pytest.mark.parametrize("app_factory", SERVICES)
def test_propagates_existing_correlation_id(app_factory):
    app = app_factory()
    client = TestClient(app)
    custom_trace_id = "trace-e2e-session-98765"

    response = client.get("/health/live", headers={CORRELATION_ID_HEADER: custom_trace_id})
    assert response.status_code == 200
    assert response.headers.get(CORRELATION_ID_HEADER) == custom_trace_id
