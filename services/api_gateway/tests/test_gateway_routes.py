"""Tests for API Gateway proxy routing, tenant context forwarding, and error delegation (Phase 11)."""

from uuid import uuid4

import httpx
import pytest
from api_gateway.main import create_app
from fastapi import status
from fastapi.testclient import TestClient


@pytest.fixture
def gateway_client():
    app = create_app()
    return TestClient(app)


def test_gateway_create_research_job_forwarding(gateway_client, monkeypatch):
    """Test POST /api/v1/research/jobs forwards headers and payload to orchestrator."""
    job_id = str(uuid4())

    async def mock_post(client_self, url, *args, **kwargs):
        assert "8001" in url
        assert kwargs["headers"]["X-Tenant-ID"] == "tenant_pharma"
        assert kwargs["headers"]["X-User-ID"] == "user_42"
        return httpx.Response(
            status_code=status.HTTP_202_ACCEPTED,
            json={
                "research_id": job_id,
                "status": "queued",
                "query": "CRISPR-Cas9 Therapeutics",
                "tenant_id": "tenant_pharma",
                "message": "Queued",
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    resp = gateway_client.post(
        "/api/v1/research/jobs",
        json={"query": "CRISPR-Cas9 Therapeutics", "tenant_id": "tenant_pharma"},
        headers={"X-Tenant-ID": "tenant_pharma", "X-User-ID": "user_42"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["research_id"] == job_id
    assert data["tenant_id"] == "tenant_pharma"


def test_gateway_get_job_status_forwarding(gateway_client, monkeypatch):
    """Test GET /api/v1/research/jobs/{job_id} forwards query to orchestrator."""
    job_id = str(uuid4())

    async def mock_get(client_self, url, *args, **kwargs):
        assert f"/api/v1/research/jobs/{job_id}" in url
        return httpx.Response(
            status_code=status.HTTP_200_OK,
            json={
                "research_id": job_id,
                "tenant_id": "tenant_pharma",
                "query": "CRISPR-Cas9",
                "status": "researching",
                "created_at": "2026-11-02T12:00:00Z",
                "is_active": True,
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    resp = gateway_client.get(
        f"/api/v1/research/jobs/{job_id}",
        headers={"X-Tenant-ID": "tenant_pharma"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["research_id"] == job_id
    assert data["status"] == "researching"


def test_gateway_document_upload_forwarding(gateway_client, monkeypatch):
    """Test POST /api/v1/documents/upload forwards multipart file stream."""

    async def mock_post(client_self, url, *args, **kwargs):
        assert "8002" in url
        return httpx.Response(
            status_code=status.HTTP_201_CREATED,
            json={
                "document_id": str(uuid4()),
                "filename": "crispr_study.pdf",
                "storage_key": "docs/crispr_study.pdf",
                "content_hash": "abc123hash",
                "byte_size": 1024,
                "page_count": 2,
                "chunk_count": 4,
                "status": "completed",
                "error_message": None,
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    files = {"file": ("crispr_study.pdf", b"%PDF-1.4 test document content", "application/pdf")}
    data = {"tenant_id": "tenant_pharma"}

    resp = gateway_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data,
        headers={"X-Tenant-ID": "tenant_pharma"},
    )
    assert resp.status_code == 201
    res_data = resp.json()
    assert res_data["filename"] == "crispr_study.pdf"
    assert res_data["chunk_count"] == 4
