"""002_flagsmith_schema

Revision ID: 002_flagsmith_schema
Revises: 001_initial_schema
Create Date: 2026-11-24 18:38:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = '002_flagsmith_schema'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Flagsmith Connections
    op.create_table(
        'flagsmith_connections',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('api_url', sa.String(length=255), nullable=False),
        sa.Column('encrypted_token', sa.Text(), nullable=False),
        sa.Column('connection_type', sa.Enum('CLOUD', 'SELF_HOSTED', name='flagsmithconnectiontype'), nullable=False),
        sa.Column('status', sa.Enum('CONNECTED', 'ERROR', 'DISCONNECTED', name='flagsmithconnectionstatus'), nullable=False),
        sa.Column('webhook_secret', sa.String(length=255), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_flagsmith_connections_org_id', 'flagsmith_connections', ['organization_id'])
    op.create_index('ix_flagsmith_org_status', 'flagsmith_connections', ['organization_id', 'status'])

    # 2. Sync Histories
    op.create_table(
        'sync_histories',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('connection_id', GUID(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', name='syncstatus'), nullable=False),
        sa.Column('trigger', sa.Enum('MANUAL', 'SCHEDULED', 'WEBHOOK', name='synctrigger'), nullable=False),
        sa.Column('records_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_updated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_unchanged', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['flagsmith_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sync_histories_org_id', 'sync_histories', ['organization_id'])
    op.create_index('ix_sync_histories_conn_id', 'sync_histories', ['connection_id'])

    # 3. Webhook Events
    op.create_table(
        'webhook_events',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('connection_id', GUID(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('signature', sa.String(length=255), nullable=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('PROCESSED', 'IGNORED', 'FAILED', name='webhookstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['flagsmith_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_webhook_events_org_id', 'webhook_events', ['organization_id'])
    op.create_index('ix_webhook_events_conn_id', 'webhook_events', ['connection_id'])

    # 4. Feature Flags
    op.create_table(
        'feature_flags',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('project_id', GUID(), nullable=False),
        sa.Column('flagsmith_feature_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum('FLAG', 'CONFIG', 'MULTIVARIATE', name='featureflagtype'), nullable=False),
        sa.Column('default_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'key', name='uq_project_flag_key')
    )
    op.create_index('ix_feature_flags_project_id', 'feature_flags', ['project_id'])
    op.create_index('ix_flags_project_key', 'feature_flags', ['project_id', 'key'])

    # 5. Feature Flag States
    op.create_table(
        'feature_flag_states',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('feature_flag_id', GUID(), nullable=False),
        sa.Column('environment_id', GUID(), nullable=False),
        sa.Column('flagsmith_feature_state_id', sa.String(length=255), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['feature_flag_id'], ['feature_flags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_flag_id', 'environment_id', name='uq_flag_environment')
    )
    op.create_index('ix_flag_state_env', 'feature_flag_states', ['feature_flag_id', 'environment_id'])


def downgrade() -> None:
    op.drop_table('feature_flag_states')
    op.drop_table('feature_flags')
    op.drop_table('webhook_events')
    op.drop_table('sync_histories')
    op.drop_table('flagsmith_connections')
    op.execute('DROP TYPE IF EXISTS featureflagtype')
    op.execute('DROP TYPE IF EXISTS webhookstatus')
    op.execute('DROP TYPE IF EXISTS synctrigger')
    op.execute('DROP TYPE IF EXISTS syncstatus')
    op.execute('DROP TYPE IF EXISTS flagsmithconnectionstatus')
    op.execute('DROP TYPE IF EXISTS flagsmithconnectiontype')
