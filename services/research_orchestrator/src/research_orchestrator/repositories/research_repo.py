"""SQLAlchemy implementation of the ResearchRepository."""

from uuid import UUID

from atlas_contracts.domain import ResearchCreate, ResearchStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_orchestrator.db.base import get_utc_now
from research_orchestrator.db.models import ResearchModel
from research_orchestrator.repositories.interfaces import ResearchRepositoryProtocol


class DuplicateIdempotencyKeyError(ValueError):
    """Raised when an idempotency key conflict occurs with different payload parameters."""

    pass


class ResearchNotFoundError(ValueError):
    """Raised when an operation targets a non-existent research ID."""

    pass


class SQLAlchemyResearchRepository(ResearchRepositoryProtocol):
    """Repository managing research lifecycle records via SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ResearchCreate) -> ResearchModel:
        """Create a new research run, respecting idempotency keys."""
        if data.idempotency_key:
            existing = await self.get_by_idempotency_key(data.idempotency_key, data.tenant_id)
            if existing is not None:
                if existing.query != data.query:
                    raise DuplicateIdempotencyKeyError(
                        f"Idempotency key '{data.idempotency_key}' was previously used for a different query"
                    )
                return existing

        record = ResearchModel(
            tenant_id=data.tenant_id,
            query=data.query,
            scope=data.scope,
            status=ResearchStatus.QUEUED.value,
            idempotency_key=data.idempotency_key,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, research_id: UUID) -> ResearchModel | None:
        """Fetch research record by primary key UUID."""
        stmt = select(ResearchModel).where(ResearchModel.id == research_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self, idempotency_key: str, tenant_id: str = "default"
    ) -> ResearchModel | None:
        """Fetch research record matching an idempotency key within a tenant boundary."""
        stmt = select(ResearchModel).where(
            ResearchModel.idempotency_key == idempotency_key,
            ResearchModel.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        research_id: UUID,
        status: ResearchStatus,
        error_details: dict | None = None,
    ) -> ResearchModel:
        """Update the lifecycle status and completion timestamp of a research run."""
        record = await self.get_by_id(research_id)
        if record is None:
            raise ResearchNotFoundError(f"Research run with ID '{research_id}' was not found")

        record.status = status.value
        if error_details is not None:
            record.error_details = error_details

        terminal_states = {
            ResearchStatus.COMPLETED.value,
            ResearchStatus.FAILED.value,
            ResearchStatus.CANCELLED.value,
            ResearchStatus.PARTIALLY_COMPLETED.value,
        }
        if status.value in terminal_states:
            record.completed_at = get_utc_now()

        await self._session.flush()
        return record

    async def list_by_tenant(
        self, tenant_id: str = "default", limit: int = 50, offset: int = 0
    ) -> list[ResearchModel]:
        """List research runs belonging to a specific tenant with pagination."""
        stmt = (
            select(ResearchModel)
            .where(ResearchModel.tenant_id == tenant_id)
            .order_by(ResearchModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
