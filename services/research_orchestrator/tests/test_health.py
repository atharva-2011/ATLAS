"""Unit tests for Research Orchestrator health and root endpoints."""

from fastapi.testclient import TestClient
from research_orchestrator.core.config import Settings
from research_orchestrator.main import create_app


def test_research_orchestrator_liveness():
    test_settings = Settings(service_name="research-orchestrator-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "research-orchestrator-test"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_research_orchestrator_readiness():
    test_settings = Settings(service_name="research-orchestrator-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "research-orchestrator-test"
    assert data["checks"]["configuration"] == "ready"


def test_research_orchestrator_root():
    test_settings = Settings(service_name="research-orchestrator-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "research-orchestrator-test"
    assert data["status"] == "running"
