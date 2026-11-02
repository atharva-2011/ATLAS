"""Unit tests for Agent Runtime health and root endpoints."""

from agent_runtime.core.config import Settings
from agent_runtime.main import create_app
from fastapi.testclient import TestClient


def test_agent_runtime_liveness():
    test_settings = Settings(service_name="agent-runtime-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "agent-runtime-test"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_agent_runtime_readiness():
    test_settings = Settings(service_name="agent-runtime-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "agent-runtime-test"
    assert data["checks"]["configuration"] == "ready"


def test_agent_runtime_root():
    test_settings = Settings(service_name="agent-runtime-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "agent-runtime-test"
    assert data["status"] == "running"
