"""Tests for Alembic schema migrations in Research Orchestrator."""

import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_and_downgrade():
    """Verify that Alembic migrations run cleanly to head and can downgrade cleanly to base."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "migration_test.db"
        async_url = f"sqlite+aiosqlite:///{db_path}"
        sync_url = f"sqlite:///{db_path}"

        repo_root = Path(__file__).resolve().parent.parent
        ini_path = repo_root / "alembic.ini"
        script_loc = repo_root / "alembic"

        alembic_cfg = Config(str(ini_path))
        alembic_cfg.set_main_option("script_location", str(script_loc))
        alembic_cfg.set_main_option("sqlalchemy.url", async_url)

        # 1. Test Upgrade to Head
        command.upgrade(alembic_cfg, "head")

        # 2. Inspect created schema
        engine = create_engine(sync_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        expected_tables = {
            "research_runs",
            "research_tasks",
            "agent_executions",
            "research_sources",
            "research_evidence",
            "research_reports",
            "alembic_version",
        }
        assert expected_tables.issubset(tables)

        # Verify index on research_runs status and tenant_id
        indexes = {idx["name"] for idx in inspector.get_indexes("research_runs")}
        assert "ix_research_runs_status" in indexes
        assert "ix_research_runs_tenant_id" in indexes

        # 3. Test Downgrade to Base
        command.downgrade(alembic_cfg, "base")

        inspector_after = inspect(engine)
        tables_after = set(inspector_after.get_table_names())
        assert "research_runs" not in tables_after
        assert "research_tasks" not in tables_after
        assert "research_evidence" not in tables_after
        assert "research_reports" not in tables_after

        engine.dispose()
