"""SQLAlchemy implementation of the TaskRepository."""

from uuid import UUID

from atlas_contracts.domain import AgentExecutionCreate, ResearchTaskCreate, TaskStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_orchestrator.db.models import AgentExecutionModel, ResearchTaskModel
from research_orchestrator.repositories.interfaces import TaskRepositoryProtocol


class TaskNotFoundError(ValueError):
    """Raised when an operation targets a non-existent task ID."""

    pass


class SQLAlchemyTaskRepository(TaskRepositoryProtocol):
    """Repository managing research tasks and agent execution attempts via SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ResearchTaskCreate) -> ResearchTaskModel:
        """Create and persist an individual research subtask."""
        record = ResearchTaskModel(
            research_id=data.research_id,
            objective=data.objective,
            agent_type=data.agent_type,
            status=TaskStatus.PENDING.value,
            priority=data.priority,
            attempts=0,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def create_many(self, tasks: list[ResearchTaskCreate]) -> list[ResearchTaskModel]:
        """Bulk-create multiple decomposed subtasks for a research plan."""
        records = [
            ResearchTaskModel(
                research_id=t.research_id,
                objective=t.objective,
                agent_type=t.agent_type,
                status=TaskStatus.PENDING.value,
                priority=t.priority,
                attempts=0,
            )
            for t in tasks
        ]
        self._session.add_all(records)
        await self._session.flush()
        return records

    async def get_by_id(self, task_id: UUID) -> ResearchTaskModel | None:
        """Fetch task by primary key UUID."""
        stmt = select(ResearchTaskModel).where(ResearchTaskModel.id == task_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_research_id(self, research_id: UUID) -> list[ResearchTaskModel]:
        """List all tasks registered under a research run, ordered by priority."""
        stmt = (
            select(ResearchTaskModel)
            .where(ResearchTaskModel.research_id == research_id)
            .order_by(ResearchTaskModel.priority.asc(), ResearchTaskModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, task_id: UUID, status: TaskStatus, increment_attempts: bool = False
    ) -> ResearchTaskModel:
        """Update the lifecycle status of a task and optionally increment attempt count."""
        record = await self.get_by_id(task_id)
        if record is None:
            raise TaskNotFoundError(f"Task with ID '{task_id}' was not found")

        record.status = status.value
        if increment_attempts:
            record.attempts += 1

        await self._session.flush()
        return record

    async def record_execution(self, data: AgentExecutionCreate) -> AgentExecutionModel:
        """Record an agent execution attempt against a task."""
        record = AgentExecutionModel(
            task_id=data.task_id,
            agent_id=data.agent_id,
            model=data.model,
            prompt_version=data.prompt_version,
        )
        self._session.add(record)
        await self._session.flush()
        return record
