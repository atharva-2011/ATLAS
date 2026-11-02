"""SQLAlchemy implementation of the EvidenceRepository."""

from uuid import UUID

from atlas_contracts.domain import EvidenceCreate, SourceCreate, VerificationStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_orchestrator.db.models import EvidenceModel, SourceModel
from research_orchestrator.repositories.interfaces import EvidenceRepositoryProtocol


class EvidenceNotFoundError(ValueError):
    """Raised when an operation targets a non-existent evidence ID."""

    pass


class SQLAlchemyEvidenceRepository(EvidenceRepositoryProtocol):
    """Repository managing sources and verified factual evidence via SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_source(self, data: SourceCreate) -> SourceModel:
        """Register a source document or external URL."""
        record = SourceModel(
            research_id=data.research_id,
            source_type=data.source_type.value,
            url=data.url,
            title=data.title,
            publisher=data.publisher,
            published_at=data.published_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def add_evidence(self, data: EvidenceCreate) -> EvidenceModel:
        """Capture an immutable factual evidence passage with locator."""
        record = EvidenceModel(
            source_id=data.source_id,
            task_id=data.task_id,
            passage=data.passage,
            claim=data.claim,
            locator=data.locator,
            verification_status=data.verification_status.value,
            confidence=data.confidence,
            content_hash=data.content_hash,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_evidence_by_id(self, evidence_id: UUID) -> EvidenceModel | None:
        """Fetch an evidence record by primary key UUID."""
        stmt = select(EvidenceModel).where(EvidenceModel.id == evidence_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_evidence_by_task(self, task_id: UUID) -> list[EvidenceModel]:
        """List all evidence captured under a specific research task."""
        stmt = (
            select(EvidenceModel)
            .where(EvidenceModel.task_id == task_id)
            .order_by(EvidenceModel.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_evidence_by_research(self, research_id: UUID) -> list[EvidenceModel]:
        """List all evidence captured across all sources belonging to a research run."""
        stmt = (
            select(EvidenceModel)
            .join(SourceModel, EvidenceModel.source_id == SourceModel.id)
            .where(SourceModel.research_id == research_id)
            .order_by(EvidenceModel.id.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_verification_status(
        self,
        evidence_id: UUID,
        status: VerificationStatus,
        confidence: float | None = None,
    ) -> EvidenceModel:
        """Update the grounding verification classification of an evidence record."""
        record = await self.get_evidence_by_id(evidence_id)
        if record is None:
            raise EvidenceNotFoundError(f"Evidence with ID '{evidence_id}' was not found")

        record.verification_status = status.value
        if confidence is not None:
            record.confidence = confidence

        await self._session.flush()
        return record
