"""SQLAlchemy implementation of the ReportRepository."""

from uuid import UUID

from atlas_contracts.domain import ReportCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_orchestrator.db.models import ReportModel
from research_orchestrator.repositories.interfaces import ReportRepositoryProtocol


class SQLAlchemyReportRepository(ReportRepositoryProtocol):
    """Repository managing generated research synthesis reports via SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ReportCreate) -> ReportModel:
        """Create and persist a research report version."""
        record = ReportModel(
            research_id=data.research_id,
            version=data.version,
            title=data.title,
            summary=data.summary,
            markdown_content=data.markdown_content,
            structured_json=data.structured_json,
            format=data.format,
            status=data.status.value,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_latest_by_research_id(self, research_id: UUID) -> ReportModel | None:
        """Fetch the highest version report generated for a research run."""
        stmt = (
            select(ReportModel)
            .where(ReportModel.research_id == research_id)
            .order_by(ReportModel.version.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_versions(self, research_id: UUID) -> list[ReportModel]:
        """List all report versions for a research run, ordered chronologically."""
        stmt = (
            select(ReportModel)
            .where(ReportModel.research_id == research_id)
            .order_by(ReportModel.version.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
