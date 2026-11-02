"""Integration tests for Ingestion Service upload endpoint."""

import io

from fastapi.testclient import TestClient
from ingestion_service.main import create_app


def test_upload_txt_file():
    app = create_app()
    client = TestClient(app)

    file_bytes = b"# Machine Learning\nAn overview of deep neural architectures."
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("overview.txt", io.BytesIO(file_bytes), "text/plain")},
        data={"tenant_id": "test_tenant"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "overview.txt"
    assert data["status"] == "completed"
    assert data["chunk_count"] >= 1
    assert data["byte_size"] == len(file_bytes)


def test_upload_empty_file_rejected():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_unsupported_extension_rejected():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("executable.exe", io.BytesIO(b"binary_junk"), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "not permitted" in response.json()["detail"]
