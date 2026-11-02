"""Repository protocols (interfaces) defining data access boundaries for Research Orchestrator."""

from typing import Protocol
from uuid import UUID

from atlas_contracts.domain import (
    AgentExecutionCreate,
    EvidenceCreate,
    ReportCreate,
    ResearchCreate,
    ResearchStatus,
    ResearchTaskCreate,
    SourceCreate,
    TaskStatus,
    VerificationStatus,
)

from research_orchestrator.db.models import (
    AgentExecutionModel,
    EvidenceModel,
    ReportModel,
    ResearchModel,
    ResearchTaskModel,
    SourceModel,
)


class ResearchRepositoryProtocol(Protocol):
    """Data access interface for research run lifecycles."""

    async def create(self, data: ResearchCreate) -> ResearchModel: ...
    async def get_by_id(self, research_id: UUID) -> ResearchModel | None: ...
    async def get_by_idempotency_key(
        self, idempotency_key: str, tenant_id: str = "default"
    ) -> ResearchModel | None: ...
    async def update_status(
        self,
        research_id: UUID,
        status: ResearchStatus,
        error_details: dict | None = None,
    ) -> ResearchModel: ...
    async def list_by_tenant(
        self, tenant_id: str = "default", limit: int = 50, offset: int = 0
    ) -> list[ResearchModel]: ...


class TaskRepositoryProtocol(Protocol):
    """Data access interface for research tasks and agent execution attempts."""

    async def create(self, data: ResearchTaskCreate) -> ResearchTaskModel: ...
    async def create_many(self, tasks: list[ResearchTaskCreate]) -> list[ResearchTaskModel]: ...
    async def get_by_id(self, task_id: UUID) -> ResearchTaskModel | None: ...
    async def list_by_research_id(self, research_id: UUID) -> list[ResearchTaskModel]: ...
    async def update_status(
        self, task_id: UUID, status: TaskStatus, increment_attempts: bool = False
    ) -> ResearchTaskModel: ...
    async def record_execution(self, data: AgentExecutionCreate) -> AgentExecutionModel: ...


class EvidenceRepositoryProtocol(Protocol):
    """Data access interface for sources and verifiable factual evidence."""

    async def add_source(self, data: SourceCreate) -> SourceModel: ...
    async def add_evidence(self, data: EvidenceCreate) -> EvidenceModel: ...
    async def get_evidence_by_id(self, evidence_id: UUID) -> EvidenceModel | None: ...
    async def list_evidence_by_task(self, task_id: UUID) -> list[EvidenceModel]: ...
    async def list_evidence_by_research(self, research_id: UUID) -> list[EvidenceModel]: ...
    async def update_verification_status(
        self,
        evidence_id: UUID,
        status: VerificationStatus,
        confidence: float | None = None,
    ) -> EvidenceModel: ...


class ReportRepositoryProtocol(Protocol):
    """Data access interface for generated research reports."""

    async def create(self, data: ReportCreate) -> ReportModel: ...
    async def get_latest_by_research_id(self, research_id: UUID) -> ReportModel | None: ...
    async def list_versions(self, research_id: UUID) -> list[ReportModel]: ...
