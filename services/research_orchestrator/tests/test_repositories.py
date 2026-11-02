"""Async repository unit and integration tests for Research Orchestrator."""

from uuid import uuid4

import pytest
from atlas_contracts.domain import (
    AgentExecutionCreate,
    EvidenceCreate,
    ReportCreate,
    ReportStatus,
    ResearchCreate,
    ResearchStatus,
    ResearchTaskCreate,
    SourceCreate,
    SourceType,
    TaskStatus,
    VerificationStatus,
)
from research_orchestrator.db.base import Base
from research_orchestrator.repositories.evidence_repo import (
    EvidenceNotFoundError,
    SQLAlchemyEvidenceRepository,
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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def async_db_session():
    """Create a pristine in-memory SQLite async session for repository testing."""
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


@pytest.mark.anyio
async def test_research_lifecycle_and_idempotency(async_db_session: AsyncSession):
    repo = SQLAlchemyResearchRepository(async_db_session)

    # 1. Create a research run
    create_dto = ResearchCreate(
        query="Investigate multi-agent consensus mechanisms",
        scope={"depth": "broad"},
        tenant_id="tenant-1",
        idempotency_key="idemp-key-001",
    )
    research = await repo.create(create_dto)
    await async_db_session.commit()

    assert research.id is not None
    assert research.query == "Investigate multi-agent consensus mechanisms"
    assert research.status == ResearchStatus.QUEUED.value
    assert research.completed_at is None

    # 2. Duplicate submission with exact same idempotency key and query -> returns existing
    duplicate = await repo.create(create_dto)
    assert duplicate.id == research.id

    # 3. Duplicate submission with same key but different query -> raises conflict
    conflict_dto = ResearchCreate(
        query="A completely different question",
        tenant_id="tenant-1",
        idempotency_key="idemp-key-001",
    )
    with pytest.raises(DuplicateIdempotencyKeyError):
        await repo.create(conflict_dto)

    # 4. Status update to PLANNING
    updated = await repo.update_status(research.id, ResearchStatus.PLANNING)
    await async_db_session.commit()
    assert updated.status == ResearchStatus.PLANNING.value
    assert updated.completed_at is None

    # 5. Status update to terminal COMPLETED
    completed = await repo.update_status(research.id, ResearchStatus.COMPLETED)
    await async_db_session.commit()
    assert completed.status == ResearchStatus.COMPLETED.value
    assert completed.completed_at is not None

    # 6. Non-existent research update raises error
    with pytest.raises(ResearchNotFoundError):
        await repo.update_status(uuid4(), ResearchStatus.FAILED)


@pytest.mark.anyio
async def test_tenant_isolation(async_db_session: AsyncSession):
    repo = SQLAlchemyResearchRepository(async_db_session)

    await repo.create(ResearchCreate(query="Tenant A Question 1", tenant_id="tenant-A"))
    await repo.create(ResearchCreate(query="Tenant A Question 2", tenant_id="tenant-A"))
    await repo.create(ResearchCreate(query="Tenant B Question 1", tenant_id="tenant-B"))
    await async_db_session.commit()

    tenant_a_runs = await repo.list_by_tenant("tenant-A")
    assert len(tenant_a_runs) == 2
    assert all(r.tenant_id == "tenant-A" for r in tenant_a_runs)

    tenant_b_runs = await repo.list_by_tenant("tenant-B")
    assert len(tenant_b_runs) == 1
    assert tenant_b_runs[0].tenant_id == "tenant-B"


@pytest.mark.anyio
async def test_tasks_and_agent_execution_recording(async_db_session: AsyncSession):
    research_repo = SQLAlchemyResearchRepository(async_db_session)
    task_repo = SQLAlchemyTaskRepository(async_db_session)

    research = await research_repo.create(ResearchCreate(query="Autonomous diagnostics review"))
    await async_db_session.commit()

    # 1. Bulk create tasks
    tasks = await task_repo.create_many(
        [
            ResearchTaskCreate(
                research_id=research.id,
                objective="Review FDA guidelines",
                agent_type="regulatory_researcher",
                priority=1,
            ),
            ResearchTaskCreate(
                research_id=research.id,
                objective="Analyze clinical study metrics",
                agent_type="analyst_agent",
                priority=2,
            ),
        ]
    )
    await async_db_session.commit()
    assert len(tasks) == 2

    # 2. Verify priority ordering
    listed_tasks = await task_repo.list_by_research_id(research.id)
    assert listed_tasks[0].priority == 1
    assert listed_tasks[1].priority == 2

    # 3. Update task status and attempts
    task_1 = listed_tasks[0]
    updated_task = await task_repo.update_status(
        task_1.id, TaskStatus.IN_PROGRESS, increment_attempts=True
    )
    await async_db_session.commit()
    assert updated_task.status == TaskStatus.IN_PROGRESS.value
    assert updated_task.attempts == 1

    # 4. Record agent execution attempt
    exec_record = await task_repo.record_execution(
        AgentExecutionCreate(
            task_id=task_1.id,
            agent_id="regulatory_researcher_v1",
            model="gpt-4o",
            prompt_version="v2.1",
        )
    )
    await async_db_session.commit()
    assert exec_record.id is not None
    assert exec_record.agent_id == "regulatory_researcher_v1"

    with pytest.raises(TaskNotFoundError):
        await task_repo.update_status(uuid4(), TaskStatus.COMPLETED)


@pytest.mark.anyio
async def test_evidence_and_sources_provenance(async_db_session: AsyncSession):
    research_repo = SQLAlchemyResearchRepository(async_db_session)
    task_repo = SQLAlchemyTaskRepository(async_db_session)
    evidence_repo = SQLAlchemyEvidenceRepository(async_db_session)

    research = await research_repo.create(ResearchCreate(query="Healthcare AI Regulation"))
    task = await task_repo.create(
        ResearchTaskCreate(
            research_id=research.id,
            objective="Examine EU AI Act Article 6",
            agent_type="regulatory_researcher",
        )
    )
    await async_db_session.commit()

    # 1. Add Source
    source = await evidence_repo.add_source(
        SourceCreate(
            research_id=research.id,
            source_type=SourceType.WEB,
            url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
            title="EU Artificial Intelligence Act",
            publisher="Official Journal of the European Union",
        )
    )
    await async_db_session.commit()
    assert source.id is not None
    assert source.source_type == SourceType.WEB.value

    # 2. Add Evidence
    evidence = await evidence_repo.add_evidence(
        EvidenceCreate(
            source_id=source.id,
            task_id=task.id,
            passage="High-risk AI systems shall be subject to conformity assessment.",
            claim="EU AI Act subjects high-risk systems to strict conformity assessments.",
            locator={"article": "6", "paragraph": "2"},
            verification_status=VerificationStatus.PENDING,
            confidence=0.98,
            content_hash="sha256:fedcba987654321",
        )
    )
    await async_db_session.commit()
    assert evidence.verification_status == VerificationStatus.PENDING.value

    # 3. Update Verification Status
    verified = await evidence_repo.update_verification_status(
        evidence.id, VerificationStatus.SUPPORTED, confidence=0.99
    )
    await async_db_session.commit()
    assert verified.verification_status == VerificationStatus.SUPPORTED.value
    assert verified.confidence == 0.99

    # 4. List evidence by research run
    all_evidence = await evidence_repo.list_evidence_by_research(research.id)
    assert len(all_evidence) == 1
    assert all_evidence[0].id == evidence.id

    with pytest.raises(EvidenceNotFoundError):
        await evidence_repo.update_verification_status(uuid4(), VerificationStatus.CONTRADICTED)


@pytest.mark.anyio
async def test_report_versioning(async_db_session: AsyncSession):
    research_repo = SQLAlchemyResearchRepository(async_db_session)
    report_repo = SQLAlchemyReportRepository(async_db_session)

    research = await research_repo.create(ResearchCreate(query="Synthesize Findings"))
    await async_db_session.commit()

    # 1. Version 1 (Draft)
    rep_v1 = await report_repo.create(
        ReportCreate(
            research_id=research.id,
            version=1,
            title="AI In Healthcare Report (Draft)",
            summary="Initial findings overview",
            markdown_content="# Draft Report\nFindings pending critic review.",
            status=ReportStatus.DRAFT,
        )
    )
    await async_db_session.commit()
    assert rep_v1.version == 1

    # 2. Version 2 (Final)
    rep_v2 = await report_repo.create(
        ReportCreate(
            research_id=research.id,
            version=2,
            title="AI In Healthcare Report (Final)",
            summary="Final executive synthesis with verified citations",
            markdown_content="# Final Report\nAll claims verified.",
            status=ReportStatus.FINAL,
        )
    )
    await async_db_session.commit()
    assert rep_v2.version == 2

    # 3. Fetch latest
    latest = await report_repo.get_latest_by_research_id(research.id)
    assert latest is not None
    assert latest.version == 2
    assert latest.status == ReportStatus.FINAL.value

    # 4. List all versions
    versions = await report_repo.list_versions(research.id)
    assert len(versions) == 2
    assert versions[0].version == 1
    assert versions[1].version == 2
