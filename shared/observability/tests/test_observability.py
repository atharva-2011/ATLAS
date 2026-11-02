"""Tests for atlas_observability package."""

import json
import logging

from atlas_observability import (
    CORRELATION_ID_HEADER,
    ConsoleFormatter,
    CorrelationIdMiddleware,
    JsonFormatter,
    get_correlation_id,
    reset_correlation_id,
    set_correlation_id,
    setup_logging,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_context_management():
    assert get_correlation_id() is None
    token = set_correlation_id("test-corr-123")
    assert get_correlation_id() == "test-corr-123"
    reset_correlation_id(token)
    assert get_correlation_id() is None


def test_console_formatter():
    formatter = ConsoleFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test console log",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "corr-xyz"
    record.service_name = "test-service"
    formatted = formatter.format(record)
    assert "[INFO ]" in formatted
    assert "[test-service]" in formatted
    assert "[corr:corr-xyz]" in formatted
    assert "Test console log" in formatted


def test_json_formatter():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.WARNING,
        pathname="test.py",
        lineno=20,
        msg="Warning message in JSON",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "corr-json-123"
    record.service_name = "json-service"
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["level"] == "WARNING"
    assert data["service"] == "json-service"
    assert data["correlation_id"] == "corr-json-123"
    assert data["message"] == "Warning message in JSON"


def test_setup_logging():
    logger = setup_logging(service_name="test_service", log_level="DEBUG", log_format="console")
    assert logger.name == "test_service"


def test_correlation_middleware_generates_id():
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/test")
    def sample_endpoint():
        return {"current_corr_id": get_correlation_id()}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
    assert CORRELATION_ID_HEADER in response.headers
    generated_id = response.headers[CORRELATION_ID_HEADER]
    assert len(generated_id) > 0
    assert response.json()["current_corr_id"] == generated_id


def test_correlation_middleware_preserves_valid_id():
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/test")
    def sample_endpoint():
        return {"current_corr_id": get_correlation_id()}

    client = TestClient(app)
    custom_id = "custom-trace-uuid-999"
    response = client.get("/test", headers={CORRELATION_ID_HEADER: custom_id})
    assert response.status_code == 200
    assert response.headers[CORRELATION_ID_HEADER] == custom_id
    assert response.json()["current_corr_id"] == custom_id
