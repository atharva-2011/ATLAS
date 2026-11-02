"""Unit tests for API Gateway health and root endpoints."""

from api_gateway.core.config import Settings
from api_gateway.main import create_app
from fastapi.testclient import TestClient


def test_api_gateway_liveness():
    test_settings = Settings(service_name="api-gateway-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "api-gateway-test"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_api_gateway_readiness():
    test_settings = Settings(service_name="api-gateway-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "api-gateway-test"
    assert data["checks"]["configuration"] == "ready"


def test_api_gateway_root():
    test_settings = Settings(service_name="api-gateway-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "api-gateway-test"
    assert data["status"] == "running"
