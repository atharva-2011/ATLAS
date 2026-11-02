"""Tests for asynchronous research job worker, endpoints, status polling, cancellation, and tenant scoping (Phase 11)."""

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from atlas_contracts.domain import ResearchStatus
from fastapi.testclient import TestClient
from research_orchestrator.db.base import Base
from research_orchestrator.db.session import get_db_session
from research_orchestrator.main import create_app
from research_orchestrator.workflow.worker import ResearchJobWorkerManager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_test_session():
    """Create in-memory SQLite database sessionmaker for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def mock_worker_manager():
    """Provide a worker manager with mocked workflow execution."""
    runner_mock = AsyncMock()
    runner_mock.execute_run = AsyncMock(
        return_value={
            "research_id": str(uuid4()),
            "status": "completed",
            "accumulated_evidence": [{"claim": "Evidence 1"}],
            "final_report": {"title": "Test Report", "markdown_content": "# Report"},
            "error": None,
        }
    )
    manager = ResearchJobWorkerManager(runner=runner_mock)
    return manager


@pytest.mark.anyio
async def test_job_worker_manager_execution(async_test_session: AsyncSession):
    """Test background worker successfully processes job and tracks progress."""
    from contextlib import asynccontextmanager

    from atlas_contracts.domain import ResearchCreate
    from research_orchestrator.repositories.research_repo import SQLAlchemyResearchRepository

    # Pre-create research run record in database
    repo = SQLAlchemyResearchRepository(async_test_session)
    record = await repo.create(
        ResearchCreate(
            query="Quantum Computing in Medicine",
            tenant_id="tenant_alpha",
        )
    )
    job_id = record.id

    runner_mock = AsyncMock()
    runner_mock.execute_run = AsyncMock(
        return_value={
            "research_id": str(job_id),
            "status": "completed",
            "accumulated_evidence": [{"claim": "Test claim"}],
            "final_report": {"title": "Synthesized Report"},
            "error": None,
        }
    )
    manager = ResearchJobWorkerManager(runner=runner_mock)

    @asynccontextmanager
    async def fake_scoped_db():
        yield async_test_session

    with patch(
        "research_orchestrator.workflow.worker.scoped_db_session", side_effect=fake_scoped_db
    ):
        task = manager.submit_job(
            research_id=job_id,
            query="Quantum Computing in Medicine",
            tenant_id="tenant_alpha",
        )
        assert manager.is_active(job_id) is True
        await task
        assert manager.is_active(job_id) is False

        progress = manager.get_progress(job_id)
        assert progress is not None
        assert progress["status"] == ResearchStatus.COMPLETED.value
        assert progress["stage"] == "completed"
        assert progress["evidence_count"] == 1


@pytest.mark.anyio
async def test_job_worker_manager_cancellation():
    """Test cancelling an in-flight background job."""

    async def slow_execution(*args, **kwargs):
        await asyncio.sleep(10.0)
        return {"status": "completed"}

    runner_mock = AsyncMock()
    runner_mock.execute_run = slow_execution
    manager = ResearchJobWorkerManager(runner=runner_mock)
    job_id = uuid4()

    with patch("research_orchestrator.workflow.worker.scoped_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        manager.submit_job(
            research_id=job_id,
            query="Slow Long Task",
            tenant_id="tenant_alpha",
        )
        assert manager.is_active(job_id) is True

        cancelled = manager.cancel_job(job_id)
        assert cancelled is True
        # Allow loop to handle cancellation callback
        await asyncio.sleep(0.05)
        assert manager.is_active(job_id) is False


@pytest.mark.anyio
async def test_create_and_poll_research_job_api(
    async_test_session: AsyncSession, mock_worker_manager
):
    """Test POST /api/v1/research/jobs and GET /api/v1/research/jobs/{job_id}."""
    app = create_app()

    async def override_db():
        yield async_test_session

    app.dependency_overrides[get_db_session] = override_db

    with patch(
        "research_orchestrator.api.job_routes.get_worker_manager", return_value=mock_worker_manager
    ):
        client = TestClient(app)

        # 1. Create job
        create_resp = client.post(
            "/api/v1/research/jobs",
            json={
                "query": "Deep learning architectures for genomics",
                "tenant_id": "tenant_med",
            },
            headers={"X-Tenant-ID": "tenant_med", "X-User-ID": "researcher_1"},
        )
        assert create_resp.status_code == 202
        data = create_resp.json()
        job_id = data["research_id"]
        assert data["tenant_id"] == "tenant_med"
        assert data["status"] == "queued"

        # 2. Poll job status
        status_resp = client.get(
            f"/api/v1/research/jobs/{job_id}",
            headers={"X-Tenant-ID": "tenant_med"},
        )
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["research_id"] == job_id
        assert status_data["tenant_id"] == "tenant_med"


@pytest.mark.anyio
async def test_tenant_data_isolation(async_test_session: AsyncSession, mock_worker_manager):
    """Test tenant scoping prevents tenant_beta from viewing tenant_alpha jobs."""
    app = create_app()

    async def override_db():
        yield async_test_session

    app.dependency_overrides[get_db_session] = override_db

    with patch(
        "research_orchestrator.api.job_routes.get_worker_manager", return_value=mock_worker_manager
    ):
        client = TestClient(app)

        # Create as tenant_alpha
        create_resp = client.post(
            "/api/v1/research/jobs",
            json={
                "query": "Proprietary Alpha Algorithm",
                "tenant_id": "tenant_alpha",
            },
            headers={"X-Tenant-ID": "tenant_alpha"},
        )
        assert create_resp.status_code == 202
        job_id = create_resp.json()["research_id"]

        # Try to read as tenant_beta
        forbidden_resp = client.get(
            f"/api/v1/research/jobs/{job_id}",
            headers={"X-Tenant-ID": "tenant_beta"},
        )
        assert forbidden_resp.status_code == 403
        assert "Access denied" in forbidden_resp.json()["detail"]
