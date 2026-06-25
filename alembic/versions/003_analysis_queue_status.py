"""add analysis queue status to leads

Revision ID: 003
Revises: 002
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    analysisstatus = sa.Enum(
        "idle",
        "pending",
        "processing",
        "completed",
        "failed",
        name="analysisstatus",
    )
    analysisstatus.create(op.get_bind(), checkfirst=False)

    op.add_column(
        "leads",
        sa.Column(
            "analysis_status",
            analysisstatus,
            nullable=False,
            server_default="idle",
        ),
    )
    op.add_column("leads", sa.Column("analysis_error", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("analysis_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("analysis_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_leads_analysis_status"), "leads", ["analysis_status"], unique=False)

    op.execute(
        """
        UPDATE leads
        SET analysis_status = CASE
            WHEN is_processing = true THEN 'processing'
            WHEN temperature_score IS NOT NULL OR current_stage IS NOT NULL THEN 'completed'
            ELSE 'idle'
        END::analysisstatus
        """
    )
    op.alter_column("leads", "analysis_status", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_leads_analysis_status"), table_name="leads")
    op.drop_column("leads", "analysis_completed_at")
    op.drop_column("leads", "analysis_requested_at")
    op.drop_column("leads", "analysis_error")
    op.drop_column("leads", "analysis_status")
    op.execute("DROP TYPE IF EXISTS analysisstatus")