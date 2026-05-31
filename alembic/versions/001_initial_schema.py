"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-04-15

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tenants',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('funnel_config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'whatsapp_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.Enum('connected', 'disconnected', name='sessionstatus'), nullable=False),
        sa.Column('connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_whatsapp_sessions_tenant_id'), 'whatsapp_sessions', ['tenant_id'], unique=False)

    op.create_table(
        'leads',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('active', 'converted', 'lost', name='leadstatus'), nullable=False),
        sa.Column('current_stage', sa.String(length=100), nullable=True),
        sa.Column('temperature_score', sa.Integer(), nullable=True),
        sa.Column('is_processing', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_leads_tenant_id'), 'leads', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_leads_phone'), 'leads', ['phone'], unique=False)
    op.create_index(op.f('ix_leads_status'), 'leads', ['status'], unique=False)

    op.create_table(
        'messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('lead_id', sa.Uuid(), nullable=False),
        sa.Column('direction', sa.Enum('inbound', 'outbound', name='messagedirection'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_messages_lead_id'), 'messages', ['lead_id'], unique=False)

    op.create_table(
        'analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('lead_id', sa.Uuid(), nullable=False),
        sa.Column('temperature_score', sa.Integer(), nullable=False),
        sa.Column('current_stage', sa.String(length=100), nullable=True),
        sa.Column('conversation_summary', sa.Text(), nullable=False),
        sa.Column('qualitative_tips', sa.Text(), nullable=False),
        sa.Column('suggested_reply', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_analyses_lead_id'), 'analyses', ['lead_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_analyses_lead_id'), table_name='analyses')
    op.drop_table('analyses')
    op.drop_index(op.f('ix_messages_lead_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_leads_status'), table_name='leads')
    op.drop_index(op.f('ix_leads_phone'), table_name='leads')
    op.drop_index(op.f('ix_leads_tenant_id'), table_name='leads')
    op.drop_table('leads')
    op.drop_index(op.f('ix_whatsapp_sessions_tenant_id'), table_name='whatsapp_sessions')
    op.drop_table('whatsapp_sessions')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_tenant_id'), table_name='users')
    op.drop_table('users')
    op.drop_table('tenants')
    op.execute('DROP TYPE IF EXISTS sessionstatus')
    op.execute('DROP TYPE IF EXISTS leadstatus')
    op.execute('DROP TYPE IF EXISTS messagedirection')
