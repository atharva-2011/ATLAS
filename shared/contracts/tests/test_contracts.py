"""Tests for atlas_contracts shared models."""

from datetime import datetime
from uuid import uuid4

from atlas_contracts import (
    DocumentChunk,
    DocumentMetadata,
    DocumentStatus,
    DocumentUploadResponse,
    ErrorResponse,
    EvidenceCreate,
    HealthResponse,
    ReadinessResponse,
    ReportStatus,
    ResearchCreate,
    ResearchRead,
    ResearchStatus,
    ResearchTaskCreate,
    ResearchTaskRead,
    ServiceStatus,
    SourceCreate,
    SourceType,
    TaskStatus,
    VerificationStatus,
    get_utc_now,
)


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


def test_domain_enums():
    assert ResearchStatus.PLANNING == "planning"
    assert TaskStatus.IN_PROGRESS == "in_progress"
    assert SourceType.WEB == "web"
    assert VerificationStatus.SUPPORTED == "supported"
    assert ReportStatus.FINAL == "final"


def test_research_dtos():
    create_dto = ResearchCreate(
        query="Research autonomous agents in clinical healthcare",
        scope={"depth": "comprehensive", "year": 2026},
        tenant_id="tenant-alpha",
        idempotency_key="idem-12345",
    )
    assert create_dto.tenant_id == "tenant-alpha"
    assert create_dto.idempotency_key == "idem-12345"

    research_id = uuid4()
    read_dto = ResearchRead(
        id=research_id,
        tenant_id="tenant-alpha",
        query=create_dto.query,
        scope=create_dto.scope,
        status=ResearchStatus.QUEUED,
        idempotency_key="idem-12345",
        created_at=get_utc_now(),
    )
    assert read_dto.id == research_id
    assert read_dto.status == ResearchStatus.QUEUED


def test_task_and_evidence_dtos():
    res_id = uuid4()
    task_create = ResearchTaskCreate(
        research_id=res_id,
        objective="Analyze FDA guidance documents",
        agent_type="regulatory_researcher",
        priority=1,
    )
    task_id = uuid4()
    task_read = ResearchTaskRead(
        id=task_id,
        research_id=res_id,
        objective=task_create.objective,
        agent_type=task_create.agent_type,
        status=TaskStatus.PENDING,
        priority=1,
        attempts=0,
        created_at=get_utc_now(),
        updated_at=get_utc_now(),
    )
    assert task_read.status == TaskStatus.PENDING

    source_id = uuid4()
    source_create = SourceCreate(
        research_id=res_id,
        source_type=SourceType.WEB,
        url="https://fda.gov/guidance-ai",
        title="FDA AI Guidance 2026",
    )
    assert source_create.source_type == SourceType.WEB

    evidence_create = EvidenceCreate(
        source_id=source_id,
        task_id=task_id,
        passage="FDA requires predetermined change control plans.",
        claim="FDA mandates change control plans for adaptive AI models.",
        locator={"page": 14, "section": "3.1"},
        verification_status=VerificationStatus.SUPPORTED,
        confidence=0.95,
        content_hash="sha256:abc123def456",
    )
    assert evidence_create.confidence == 0.95
    assert evidence_create.locator["page"] == 14


def test_document_ingestion_dtos():
    doc_id = uuid4()
    meta = DocumentMetadata(
        id=doc_id,
        tenant_id="tenant-xyz",
        filename="report.pdf",
        mime_type="application/pdf",
        size_bytes=1048576,
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        page_count=12,
        status=DocumentStatus.COMPLETED,
        created_at=get_utc_now(),
    )
    assert meta.id == doc_id
    assert meta.page_count == 12
    assert meta.status == DocumentStatus.COMPLETED

    chunk_id = uuid4()
    chunk = DocumentChunk(
        id=chunk_id,
        document_id=doc_id,
        chunk_index=0,
        text="The artificial intelligence clinical trial observed significant improvements.",
        content_hash="sha256:11223344",
        locator={"page": 3, "section": "Results"},
    )
    assert chunk.id == chunk_id
    assert chunk.locator["page"] == 3

    resp = DocumentUploadResponse(
        document=meta,
        chunks_count=1,
        chunks=[chunk],
    )
    assert resp.chunks_count == 1
    assert resp.chunks[0].chunk_index == 0
