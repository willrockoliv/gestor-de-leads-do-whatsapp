"""expand whatsapp session for phase 6

Revision ID: 002
Revises: 001
Create Date: 2026-06-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("whatsapp_sessions", sa.Column("session_id", sa.String(length=255), nullable=True))
    op.add_column("whatsapp_sessions", sa.Column("qr_code", sa.Text(), nullable=True))
    op.add_column("whatsapp_sessions", sa.Column("qr_code_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("whatsapp_sessions", sa.Column("phone_number", sa.String(length=50), nullable=True))
    op.add_column("whatsapp_sessions", sa.Column("connected_since", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE whatsapp_sessions SET session_id = id::text WHERE session_id IS NULL")
    op.alter_column("whatsapp_sessions", "session_id", existing_type=sa.String(length=255), nullable=False)
    op.create_index(op.f("ix_whatsapp_sessions_session_id"), "whatsapp_sessions", ["session_id"], unique=True)

    op.execute("ALTER TYPE sessionstatus RENAME TO sessionstatus_old")
    sessionstatus_new = sa.Enum(
        "PENDING",
        "QR_CODE_READY",
        "CONNECTING",
        "CONNECTED",
        "DISCONNECTED",
        "ERROR",
        name="sessionstatus",
    )
    sessionstatus_new.create(op.get_bind(), checkfirst=False)

    op.execute(
        """
        ALTER TABLE whatsapp_sessions
        ALTER COLUMN status TYPE sessionstatus
        USING (
            CASE status::text
                WHEN 'connected' THEN 'CONNECTED'
                WHEN 'disconnected' THEN 'DISCONNECTED'
                ELSE 'ERROR'
            END
        )::sessionstatus
        """
    )
    op.execute("DROP TYPE sessionstatus_old")


def downgrade() -> None:
    op.execute("ALTER TYPE sessionstatus RENAME TO sessionstatus_new")
    sessionstatus_old = sa.Enum("connected", "disconnected", name="sessionstatus")
    sessionstatus_old.create(op.get_bind(), checkfirst=False)

    op.execute(
        """
        ALTER TABLE whatsapp_sessions
        ALTER COLUMN status TYPE sessionstatus
        USING (
            CASE status::text
                WHEN 'CONNECTED' THEN 'connected'
                ELSE 'disconnected'
            END
        )::sessionstatus
        """
    )
    op.execute("DROP TYPE sessionstatus_new")

    op.drop_index(op.f("ix_whatsapp_sessions_session_id"), table_name="whatsapp_sessions")
    op.drop_column("whatsapp_sessions", "connected_since")
    op.drop_column("whatsapp_sessions", "phone_number")
    op.drop_column("whatsapp_sessions", "qr_code_expires_at")
    op.drop_column("whatsapp_sessions", "qr_code")
    op.drop_column("whatsapp_sessions", "session_id")
