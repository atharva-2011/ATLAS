"""SQLAlchemy domain models for research orchestration and persistence."""

from datetime import datetime
from uuid import UUID

from atlas_contracts.domain import (
    ReportStatus,
    ResearchStatus,
    SourceType,
    TaskStatus,
    VerificationStatus,
)
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from research_orchestrator.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, get_utc_now


class ResearchModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted research investigation run."""

    __tablename__ = "research_runs"

    tenant_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, default="default"
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False, default=ResearchStatus.QUEUED.value
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, index=True, nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    tasks: Mapped[list["ResearchTaskModel"]] = relationship(
        "ResearchTaskModel", back_populates="research", cascade="all, delete-orphan"
    )
    sources: Mapped[list["SourceModel"]] = relationship(
        "SourceModel", back_populates="research", cascade="all, delete-orphan"
    )
    reports: Mapped[list["ReportModel"]] = relationship(
        "ReportModel", back_populates="research", cascade="all, delete-orphan"
    )


class ResearchTaskModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual decomposed subtask within a research plan."""

    __tablename__ = "research_tasks"

    research_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False, default=TaskStatus.PENDING.value
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    research: Mapped["ResearchModel"] = relationship("ResearchModel", back_populates="tasks")
    executions: Mapped[list["AgentExecutionModel"]] = relationship(
        "AgentExecutionModel", back_populates="task", cascade="all, delete-orphan"
    )
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel", back_populates="task", cascade="all, delete-orphan"
    )


class AgentExecutionModel(Base, UUIDPrimaryKeyMixin):
    """Execution attempt of an agent working on a task."""

    __tablename__ = "agent_executions"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    task: Mapped["ResearchTaskModel"] = relationship(
        "ResearchTaskModel", back_populates="executions"
    )


class SourceModel(Base, UUIDPrimaryKeyMixin):
    """External or internal source citation reference."""

    __tablename__ = "research_sources"

    research_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SourceType.WEB.value
    )
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(256), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )

    # Relationships
    research: Mapped["ResearchModel"] = relationship("ResearchModel", back_populates="sources")
    evidence: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel", back_populates="source", cascade="all, delete-orphan"
    )


class EvidenceModel(Base, UUIDPrimaryKeyMixin):
    """Extracted verifiable fact/passage tied to a source and task."""

    __tablename__ = "research_evidence"

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    passage: Mapped[str] = mapped_column(Text, nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    locator: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    verification_status: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False, default=VerificationStatus.PENDING.value
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)

    # Relationships
    source: Mapped["SourceModel"] = relationship("SourceModel", back_populates="evidence")
    task: Mapped["ResearchTaskModel"] = relationship("ResearchTaskModel", back_populates="evidence")


class ReportModel(Base, UUIDPrimaryKeyMixin):
    """Generated research synthesis report."""

    __tablename__ = "research_reports"

    research_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    format: Mapped[str] = mapped_column(String(32), default="markdown", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ReportStatus.DRAFT.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_utc_now, nullable=False
    )

    # Relationships
    research: Mapped["ResearchModel"] = relationship("ResearchModel", back_populates="reports")
