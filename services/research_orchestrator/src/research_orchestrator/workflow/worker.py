"""Background worker execution manager for asynchronous research jobs."""

import asyncio
import logging
from uuid import UUID

from atlas_contracts.domain import ResearchStatus

from research_orchestrator.db.session import scoped_db_session
from research_orchestrator.repositories.research_repo import SQLAlchemyResearchRepository
from research_orchestrator.workflow.runner import ResearchWorkflowRunner

logger = logging.getLogger(__name__)


class ResearchJobWorkerManager:
    """Manages lifecycle, active execution, cancellation, and status of async research jobs."""

    def __init__(self, runner: ResearchWorkflowRunner | None = None) -> None:
        self.runner = runner or ResearchWorkflowRunner()
        self._active_tasks: dict[UUID, asyncio.Task] = {}
        self._task_progress: dict[UUID, dict] = {}

    def submit_job(
        self,
        research_id: UUID,
        query: str,
        tenant_id: str,
        timeout_seconds: float = 300.0,
    ) -> asyncio.Task:
        """Submit an asynchronous research task into background event loop execution."""
        self._task_progress[research_id] = {
            "status": ResearchStatus.QUEUED.value,
            "progress_percent": 10,
            "stage": "job_queued",
        }

        task = asyncio.create_task(
            self._run_job_with_lifecycle(
                research_id=research_id,
                query=query,
                tenant_id=tenant_id,
                timeout_seconds=timeout_seconds,
            ),
            name=f"research_job_{research_id}",
        )
        self._active_tasks[research_id] = task

        def _cleanup(fut: asyncio.Future) -> None:
            self._active_tasks.pop(research_id, None)

        task.add_done_callback(_cleanup)
        return task

    async def _run_job_with_lifecycle(
        self,
        research_id: UUID,
        query: str,
        tenant_id: str,
        timeout_seconds: float,
    ) -> None:
        """Execute research job within timeout deadline and update database state."""
        self._task_progress[research_id] = {
            "status": ResearchStatus.RESEARCHING.value,
            "progress_percent": 25,
            "stage": "workflow_executing",
        }

        try:
            async with scoped_db_session() as session:
                repo = SQLAlchemyResearchRepository(session)
                await repo.update_status(research_id, ResearchStatus.RESEARCHING)

            # Execute workflow with timeout guard
            final_state = await asyncio.wait_for(
                self.runner.execute_run(
                    query=query,
                    research_id=research_id,
                    tenant_id=tenant_id,
                ),
                timeout=timeout_seconds,
            )

            status_val = (
                ResearchStatus.COMPLETED
                if final_state.get("status") == "completed"
                else ResearchStatus.PARTIALLY_COMPLETED
            )

            async with scoped_db_session() as session:
                repo = SQLAlchemyResearchRepository(session)
                await repo.update_status(
                    research_id=research_id,
                    status=status_val,
                    error_details={"error": final_state.get("error")}
                    if final_state.get("error")
                    else None,
                )

            self._task_progress[research_id] = {
                "status": status_val.value,
                "progress_percent": 100,
                "stage": "completed",
                "evidence_count": len(final_state.get("accumulated_evidence", [])),
                "report_available": final_state.get("final_report") is not None,
            }

        except asyncio.CancelledError:
            logger.warning("Research job %s was cancelled by user request", research_id)
            async with scoped_db_session() as session:
                repo = SQLAlchemyResearchRepository(session)
                await repo.update_status(
                    research_id=research_id,
                    status=ResearchStatus.CANCELLED,
                    error_details={"reason": "Job explicitly cancelled by client request"},
                )
            self._task_progress[research_id] = {
                "status": ResearchStatus.CANCELLED.value,
                "progress_percent": 100,
                "stage": "cancelled",
            }
            raise

        except TimeoutError:
            logger.error("Research job %s timed out after %s seconds", research_id, timeout_seconds)
            async with scoped_db_session() as session:
                repo = SQLAlchemyResearchRepository(session)
                await repo.update_status(
                    research_id=research_id,
                    status=ResearchStatus.FAILED,
                    error_details={
                        "error": f"Job execution exceeded deadline of {timeout_seconds}s"
                    },
                )
            self._task_progress[research_id] = {
                "status": ResearchStatus.FAILED.value,
                "progress_percent": 100,
                "stage": "timeout",
            }

        except Exception as exc:
            logger.exception("Research job %s failed unexpectedly: %s", research_id, exc)
            async with scoped_db_session() as session:
                repo = SQLAlchemyResearchRepository(session)
                await repo.update_status(
                    research_id=research_id,
                    status=ResearchStatus.FAILED,
                    error_details={"error": str(exc)},
                )
            self._task_progress[research_id] = {
                "status": ResearchStatus.FAILED.value,
                "progress_percent": 100,
                "stage": "error",
            }

    def cancel_job(self, research_id: UUID) -> bool:
        """Cancel a running research job if active."""
        task = self._active_tasks.get(research_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def get_progress(self, research_id: UUID) -> dict | None:
        """Retrieve in-memory real-time progress state for a job."""
        return self._task_progress.get(research_id)

    def is_active(self, research_id: UUID) -> bool:
        """Return True if the job is actively running in the background."""
        task = self._active_tasks.get(research_id)
        return bool(task and not task.done())
