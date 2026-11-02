"""initial_schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-02 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. research_runs
    op.create_table(
        "research_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_research_runs_status", "research_runs", ["status"], unique=False)
    op.create_index("ix_research_runs_tenant_id", "research_runs", ["tenant_id"], unique=False)
    op.create_index(
        "ix_research_runs_idempotency_key", "research_runs", ["idempotency_key"], unique=False
    )

    # 2. research_tasks
    op.create_table(
        "research_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("research_id", sa.Uuid(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("agent_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["research_id"], ["research_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_tasks_research_id", "research_tasks", ["research_id"], unique=False
    )
    op.create_index("ix_research_tasks_status", "research_tasks", ["status"], unique=False)

    # 3. agent_executions
    op.create_table(
        "agent_executions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["research_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_executions_task_id", "agent_executions", ["task_id"], unique=False)

    # 4. research_sources
    op.create_table(
        "research_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("research_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("publisher", sa.String(length=256), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["research_id"], ["research_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_sources_research_id", "research_sources", ["research_id"], unique=False
    )

    # 5. research_evidence
    op.create_table(
        "research_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("passage", sa.Text(), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("locator", sa.JSON(), nullable=False),
        sa.Column("verification_status", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["research_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["research_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_evidence_source_id", "research_evidence", ["source_id"], unique=False
    )
    op.create_index("ix_research_evidence_task_id", "research_evidence", ["task_id"], unique=False)
    op.create_index(
        "ix_research_evidence_verification_status",
        "research_evidence",
        ["verification_status"],
        unique=False,
    )
    op.create_index(
        "ix_research_evidence_content_hash", "research_evidence", ["content_hash"], unique=False
    )

    # 6. research_reports
    op.create_table(
        "research_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("research_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("markdown_content", sa.Text(), nullable=False),
        sa.Column("structured_json", sa.JSON(), nullable=True),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["research_id"], ["research_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_reports_research_id", "research_reports", ["research_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("research_reports")
    op.drop_table("research_evidence")
    op.drop_table("research_sources")
    op.drop_table("agent_executions")
    op.drop_table("research_tasks")
    op.drop_table("research_runs")
