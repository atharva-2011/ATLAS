"""Unit tests for Evaluation Service health and root endpoints."""

from evaluation_service.core.config import Settings
from evaluation_service.main import create_app
from fastapi.testclient import TestClient


def test_evaluation_service_liveness():
    test_settings = Settings(service_name="evaluation-service-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "evaluation-service-test"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_evaluation_service_readiness():
    test_settings = Settings(service_name="evaluation-service-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "evaluation-service-test"
    assert data["checks"]["configuration"] == "ready"


def test_evaluation_service_root():
    test_settings = Settings(service_name="evaluation-service-test", service_version="0.1.0")
    app = create_app(settings=test_settings)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "evaluation-service-test"
    assert data["status"] == "running"
