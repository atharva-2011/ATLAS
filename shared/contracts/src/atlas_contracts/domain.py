"""Domain models, enums, and data transfer objects for ATLAS research workflows."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


class ResearchStatus(StrEnum):
    """Lifecycle status of a research investigation run."""

    QUEUED = "queued"
    PLANNING = "planning"
    RESEARCHING = "researching"
    VERIFYING = "verifying"
    CRITIQUING = "critiquing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class TaskStatus(StrEnum):
    """Lifecycle status of an individual research task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class SourceType(StrEnum):
    """Categories of supporting research sources."""

    WEB = "web"
    INTERNAL_DOCUMENT = "internal_document"
    PAPER = "paper"


class VerificationStatus(StrEnum):
    """Grounding verification status of factual claims against evidence."""

    PENDING = "pending"
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    UNSUPPORTED = "unsupported"


class ReportStatus(StrEnum):
    """Status of generated research report artifacts."""

    DRAFT = "draft"
    FINAL = "final"


class DocumentStatus(StrEnum):
    """Lifecycle status of an ingested source document."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SCANNED_OCR_REQUIRED = "scanned_ocr_required"


# --- Research DTOs ---


class ResearchCreate(BaseModel):
    """Payload to initiate a new research run."""

    query: str = Field(min_length=3, description="Research question or topic")
    scope: dict[str, Any] = Field(
        default_factory=dict, description="Scope boundaries, dates, exclusions"
    )
    tenant_id: str = Field(default="default", description="Tenant ownership identifier")
    idempotency_key: str | None = Field(default=None, description="Client idempotency key")


class ResearchRead(BaseModel):
    """Representation of a persisted research run."""

    id: UUID
    tenant_id: str
    query: str
    scope: dict[str, Any]
    status: ResearchStatus
    idempotency_key: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    error_details: dict[str, Any] | None = None


# --- Task DTOs ---


class ResearchTaskCreate(BaseModel):
    """Payload to register a subtask in a research plan."""

    research_id: UUID
    objective: str = Field(min_length=3, description="Specific sub-question to investigate")
    agent_type: str = Field(description="Target agent role (e.g., web_researcher, doc_researcher)")
    priority: int = Field(default=1, ge=1, le=10, description="Execution priority (1=highest)")


class ResearchTaskRead(BaseModel):
    """Representation of a persisted research task."""

    id: UUID
    research_id: UUID
    objective: str
    agent_type: str
    status: TaskStatus
    priority: int
    attempts: int
    created_at: datetime
    updated_at: datetime


# --- Agent Execution DTOs ---


class AgentExecutionCreate(BaseModel):
    """Payload recording the invocation of an agent."""

    task_id: UUID
    agent_id: str
    model: str
    prompt_version: str | None = None


class AgentExecutionRead(BaseModel):
    """Representation of an agent execution attempt."""

    id: UUID
    task_id: UUID
    agent_id: str
    model: str
    prompt_version: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    tokens_used: int = 0
    error: str | None = None


# --- Source DTOs ---


class SourceCreate(BaseModel):
    """Payload to record an external or internal source."""

    research_id: UUID
    source_type: SourceType
    url: str | None = None
    title: str | None = None
    publisher: str | None = None
    published_at: datetime | None = None


class SourceRead(BaseModel):
    """Representation of an established source."""

    id: UUID
    research_id: UUID
    source_type: SourceType
    url: str | None = None
    title: str | None = None
    publisher: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime


# --- Evidence DTOs ---


class EvidenceCreate(BaseModel):
    """Payload capturing factual evidence linked to a source and task."""

    source_id: UUID
    task_id: UUID
    passage: str = Field(min_length=1, description="Exact text excerpt")
    claim: str = Field(min_length=1, description="Extracted claim or statement")
    locator: dict[str, Any] = Field(
        default_factory=dict, description="Page, section, or line coordinates"
    )
    verification_status: VerificationStatus = Field(default=VerificationStatus.PENDING)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    content_hash: str | None = Field(default=None, description="SHA256 of the raw passage")


class EvidenceRead(BaseModel):
    """Representation of a persisted evidence record."""

    id: UUID
    source_id: UUID
    task_id: UUID
    passage: str
    claim: str
    locator: dict[str, Any]
    verification_status: VerificationStatus
    confidence: float | None = None
    content_hash: str | None = None


# --- Report DTOs ---


class ReportCreate(BaseModel):
    """Payload creating or updating a generated research report."""

    research_id: UUID
    version: int = Field(default=1, ge=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    markdown_content: str = Field(min_length=1)
    structured_json: dict[str, Any] | None = None
    format: str = "markdown"
    status: ReportStatus = ReportStatus.DRAFT


class ReportRead(BaseModel):
    """Representation of a saved research report."""

    id: UUID
    research_id: UUID
    version: int
    title: str
    summary: str
    markdown_content: str
    structured_json: dict[str, Any] | None = None
    format: str
    status: ReportStatus
    created_at: datetime


# --- Document Ingestion DTOs ---


class DocumentMetadata(BaseModel):
    """Metadata describing an ingested document."""

    id: UUID
    tenant_id: str = "default"
    filename: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    page_count: int = 1
    status: DocumentStatus = DocumentStatus.UPLOADED
    created_at: datetime
    error_message: str | None = None


class DocumentChunk(BaseModel):
    """Normalized, locator-preserving text chunk derived from an ingested document."""

    id: UUID | None = None
    document_id: UUID
    chunk_index: int
    text: str = Field(min_length=1)
    content_hash: str
    locator: dict[str, Any] = Field(default_factory=dict)
    character_count: int | None = None


# Alias for pipeline compatibility
DocumentChunkDTO = DocumentChunk


class DocumentIngestionResult(BaseModel):
    """Result summary of processing and chunking a document."""

    document_id: UUID
    filename: str
    storage_key: str
    content_hash: str
    byte_size: int
    page_count: int
    chunk_count: int
    status: DocumentStatus
    error_message: str | None = None


class DocumentUploadResponse(BaseModel):
    """Response returned upon successful document upload and chunking."""

    document: DocumentMetadata
    chunks_count: int
    chunks: list[DocumentChunk] = Field(default_factory=list)
