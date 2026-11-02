"""Repository pattern implementations and interfaces for Research Orchestrator."""

from research_orchestrator.repositories.evidence_repo import (
    EvidenceNotFoundError,
    SQLAlchemyEvidenceRepository,
)
from research_orchestrator.repositories.interfaces import (
    EvidenceRepositoryProtocol,
    ReportRepositoryProtocol,
    ResearchRepositoryProtocol,
    TaskRepositoryProtocol,
)
from research_orchestrator.repositories.report_repo import SQLAlchemyReportRepository
from research_orchestrator.repositories.research_repo import (
    DuplicateIdempotencyKeyError,
    ResearchNotFoundError,
    SQLAlchemyResearchRepository,
)
from research_orchestrator.repositories.task_repo import (
    SQLAlchemyTaskRepository,
    TaskNotFoundError,
)

__all__ = [
    "DuplicateIdempotencyKeyError",
    "EvidenceNotFoundError",
    "EvidenceRepositoryProtocol",
    "ReportRepositoryProtocol",
    "ResearchNotFoundError",
    "ResearchRepositoryProtocol",
    "SQLAlchemyEvidenceRepository",
    "SQLAlchemyReportRepository",
    "SQLAlchemyResearchRepository",
    "SQLAlchemyTaskRepository",
    "TaskNotFoundError",
    "TaskRepositoryProtocol",
]
