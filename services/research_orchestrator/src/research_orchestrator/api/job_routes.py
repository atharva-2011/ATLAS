"""Asynchronous research job management endpoints (Phase 11)."""

from typing import Annotated, Any
from uuid import UUID

from atlas_contracts.domain import ResearchCreate, ResearchRead, ResearchStatus
from atlas_security import SecurityContext, get_security_context
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from research_orchestrator.db.session import get_db_session
from research_orchestrator.repositories.report_repo import SQLAlchemyReportRepository
from research_orchestrator.repositories.research_repo import SQLAlchemyResearchRepository
from research_orchestrator.workflow.worker import ResearchJobWorkerManager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/research/jobs", tags=["Research Jobs"])

_worker_manager: ResearchJobWorkerManager | None = None


def get_worker_manager() -> ResearchJobWorkerManager:
    """Singleton provider for background research job worker manager."""
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = ResearchJobWorkerManager()
    return _worker_manager


class JobCreateResponse(BaseModel):
    """Response returned upon submitting an asynchronous research run."""

    research_id: UUID
    status: ResearchStatus
    query: str
    tenant_id: str
    message: str


class JobStatusResponse(BaseModel):
    """Detailed status and live execution metrics for a research run."""

    research_id: UUID
    tenant_id: str
    query: str
    status: str
    created_at: str
    completed_at: str | None = None
    is_active: bool = False
    progress: dict[str, Any] | None = None
    error_details: dict[str, Any] | None = None


class JobCancellationResponse(BaseModel):
    """Confirmation of cancellation request."""

    research_id: UUID
    cancelled: bool
    status: str
    message: str


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create background asynchronous research job",
)
async def create_research_job(
    payload: ResearchCreate,
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    manager: Annotated[ResearchJobWorkerManager, Depends(get_worker_manager)],
) -> JobCreateResponse:
    """Submit research query to background worker queue, establishing a persisted job record."""
    # Enforce tenant scoping from security context if header provided
    tenant_id = ctx.tenant_id if ctx.tenant_id != "default" else payload.tenant_id
    scoped_payload = payload.model_copy(update={"tenant_id": tenant_id})

    repo = SQLAlchemyResearchRepository(session)
    record = await repo.create(scoped_payload)

    # Submit to worker queue
    manager.submit_job(
        research_id=record.id,
        query=record.query,
        tenant_id=record.tenant_id,
    )

    return JobCreateResponse(
        research_id=record.id,
        status=ResearchStatus(record.status),
        query=record.query,
        tenant_id=record.tenant_id,
        message="Research job created and queued for background processing",
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get status and live progress of research job",
)
async def get_research_job_status(
    job_id: UUID,
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    manager: Annotated[ResearchJobWorkerManager, Depends(get_worker_manager)],
) -> JobStatusResponse:
    """Fetch status, lifecycle metadata, and live progress percent for a research job."""
    repo = SQLAlchemyResearchRepository(session)
    record = await repo.get_by_id(job_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research job '{job_id}' not found",
        )

    # Enforce tenant data isolation
    if ctx.tenant_id != "default" and record.tenant_id != ctx.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: job belongs to another tenant",
        )

    is_active = manager.is_active(job_id)
    progress = manager.get_progress(job_id)

    return JobStatusResponse(
        research_id=record.id,
        tenant_id=record.tenant_id,
        query=record.query,
        status=record.status,
        created_at=record.created_at.isoformat(),
        completed_at=record.completed_at.isoformat() if record.completed_at else None,
        is_active=is_active,
        progress=progress,
        error_details=record.error_details,
    )


@router.post(
    "/{job_id}/cancel",
    response_model=JobCancellationResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel active background research job",
)
async def cancel_research_job(
    job_id: UUID,
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    manager: Annotated[ResearchJobWorkerManager, Depends(get_worker_manager)],
) -> JobCancellationResponse:
    """Request early cancellation of an active research run."""
    repo = SQLAlchemyResearchRepository(session)
    record = await repo.get_by_id(job_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research job '{job_id}' not found",
        )

    if ctx.tenant_id != "default" and record.tenant_id != ctx.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: job belongs to another tenant",
        )

    cancelled = manager.cancel_job(job_id)
    if not cancelled:
        # Check if already in terminal state
        return JobCancellationResponse(
            research_id=job_id,
            cancelled=False,
            status=record.status,
            message=f"Job was not actively running (current status: {record.status})",
        )

    # Record cancellation state in repository
    await repo.update_status(
        job_id,
        ResearchStatus.CANCELLED,
        error_details={"reason": "Cancelled via API endpoint"},
    )

    return JobCancellationResponse(
        research_id=job_id,
        cancelled=True,
        status=ResearchStatus.CANCELLED.value,
        message="Cancellation signal successfully dispatched to background worker",
    )


@router.get(
    "/{job_id}/report",
    status_code=status.HTTP_200_OK,
    summary="Retrieve final synthesized research report",
)
async def get_research_job_report(
    job_id: UUID,
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Retrieve the generated publication markdown report and structured findings."""
    repo = SQLAlchemyResearchRepository(session)
    record = await repo.get_by_id(job_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research job '{job_id}' not found",
        )

    if ctx.tenant_id != "default" and record.tenant_id != ctx.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: job belongs to another tenant",
        )

    report_repo = SQLAlchemyReportRepository(session)
    report = await report_repo.get_latest_by_research_id(job_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report is not yet generated for this research job",
        )

    return {
        "report_id": str(report.id),
        "research_id": str(report.research_id),
        "version": report.version,
        "title": report.title,
        "summary": report.summary,
        "markdown_content": report.markdown_content,
        "structured_json": report.structured_json,
        "status": report.status,
    }


@router.get(
    "",
    response_model=list[ResearchRead],
    status_code=status.HTTP_200_OK,
    summary="List tenant research jobs",
)
async def list_research_jobs(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ResearchRead]:
    """List historical and active research jobs within the current tenant."""
    repo = SQLAlchemyResearchRepository(session)
    records = await repo.list_by_tenant(tenant_id=ctx.tenant_id, limit=limit, offset=offset)
    return [
        ResearchRead(
            id=r.id,
            tenant_id=r.tenant_id,
            query=r.query,
            scope=r.scope,
            status=ResearchStatus(r.status),
            idempotency_key=r.idempotency_key,
            created_at=r.created_at,
            completed_at=r.completed_at,
            error_details=r.error_details,
        )
        for r in records
    ]
