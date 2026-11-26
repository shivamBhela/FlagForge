"""003_full_platform_schema

Revision ID: 003_full_platform_schema
Revises: 002_flagsmith_schema
Create Date: 2026-11-24 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

revision: str = '003_full_platform_schema'
down_revision: Union[str, None] = '002_flagsmith_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Repositories
    op.create_table(
        'repositories',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('project_id', GUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('repo_url', sa.String(length=512), nullable=False),
        sa.Column('default_branch', sa.String(length=100), nullable=False, server_default='main'),
        sa.Column('language', sa.String(length=50), nullable=False, server_default='typescript'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_repositories_org', 'repositories', ['organization_id'])

    # 2. Scans
    op.create_table(
        'scans',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('repository_id', GUID(), nullable=False),
        sa.Column('commit_sha', sa.String(length=40), nullable=False, server_default='HEAD'),
        sa.Column('branch', sa.String(length=100), nullable=False, server_default='main'),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', name='scanstatus'), nullable=False),
        sa.Column('files_scanned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scans_org', 'scans', ['organization_id'])

    # 3. Flag References
    op.create_table(
        'flag_references',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('scan_id', GUID(), nullable=False),
        sa.Column('repository_id', GUID(), nullable=False),
        sa.Column('flag_key', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('symbol_name', sa.String(length=255), nullable=True),
        sa.Column('parser_confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('evidence_snippet', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('CONFIRMED', 'STALE', 'UNRESOLVED', name='referencestatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_flag_references_flag', 'flag_references', ['flag_key'])
    op.create_index('ix_flag_references_org', 'flag_references', ['organization_id'])

    # 4. Dependency Edges
    op.create_table(
        'dependency_edges',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('project_id', GUID(), nullable=True),
        sa.Column('source_id', sa.String(length=255), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.Enum('FLAG', 'COMPONENT', 'SERVICE', 'API', name='nodetype'), nullable=False),
        sa.Column('target_id', sa.String(length=255), nullable=False),
        sa.Column('target_name', sa.String(length=255), nullable=False),
        sa.Column('target_type', sa.Enum('FLAG', 'COMPONENT', 'SERVICE', 'API', name='nodetype'), nullable=False),
        sa.Column('edge_type', sa.Enum('EXPLICIT', 'INFERRED', 'MANUAL', name='edgetype'), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'source_id', 'target_id', name='uq_dep_edge')
    )

    # 5. Simulation Scenarios & Runs (Chaos Lab)
    op.create_table(
        'simulation_scenarios',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('environment_name', sa.String(length=100), nullable=False, server_default='staging'),
        sa.Column('target_flag_key', sa.String(length=255), nullable=False),
        sa.Column('scenario_type', sa.String(length=50), nullable=False, server_default='TOGGLE_INVERSION'),
        sa.Column('test_traffic_rate', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'simulation_runs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('scenario_id', GUID(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'RESTORING', 'COMPLETED', 'FAILED', name='simulationstatus'), nullable=False),
        sa.Column('pre_snapshot', sa.JSON(), nullable=False),
        sa.Column('restored_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('baseline_error_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('simulated_error_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('baseline_p95_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('simulated_p95_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('log_output', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scenario_id'], ['simulation_scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Telemetry Aggregates
    op.create_table(
        'telemetry_aggregates',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('environment_name', sa.String(length=100), nullable=False, server_default='production'),
        sa.Column('feature_flag_key', sa.String(length=255), nullable=True),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('p50_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('p95_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('p99_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_telemetry_org_flag', 'telemetry_aggregates', ['organization_id', 'feature_flag_key'])

    # 7. Rollout Policies & Risk Assessments
    op.create_table(
        'rollout_policies',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('project_id', GUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('mode', sa.Enum('MONITOR', 'NOTIFY', 'APPROVAL_REQUIRED', 'AUTOMATIC', name='policymode'), nullable=False),
        sa.Column('weight_dependency_impact', sa.Float(), nullable=False, server_default='0.30'),
        sa.Column('weight_error_anomaly', sa.Float(), nullable=False, server_default='0.25'),
        sa.Column('weight_latency_anomaly', sa.Float(), nullable=False, server_default='0.20'),
        sa.Column('weight_change_criticality', sa.Float(), nullable=False, server_default='0.15'),
        sa.Column('weight_rollout_velocity', sa.Float(), nullable=False, server_default='0.10'),
        sa.Column('max_error_rate_threshold', sa.Float(), nullable=False, server_default='0.05'),
        sa.Column('max_p95_latency_ms', sa.Float(), nullable=False, server_default='500.0'),
        sa.Column('critical_risk_threshold', sa.Float(), nullable=False, server_default='75.0'),
        sa.Column('min_telemetry_samples', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('kill_switch_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'risk_assessments',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('project_id', GUID(), nullable=True),
        sa.Column('flag_key', sa.String(length=255), nullable=False),
        sa.Column('environment_name', sa.String(length=100), nullable=False, server_default='production'),
        sa.Column('calculated_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_band', sa.Enum('LOW', 'MODERATE', 'HIGH', 'CRITICAL', 'INSUFFICIENT_DATA', name='riskband'), nullable=False),
        sa.Column('dependency_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_anomaly_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency_anomaly_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('criticality_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('velocity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('factors', sa.JSON(), nullable=False),
        sa.Column('recommended_action', sa.String(length=100), nullable=False, server_default='ALLOW_ROLLOUT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. Incidents & Rollback Actions
    op.create_table(
        'incidents',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='incidentseverity'), nullable=False),
        sa.Column('status', sa.Enum('DETECTED', 'INVESTIGATING', 'ROLLED_BACK', 'RESOLVED', name='incidentstatus'), nullable=False),
        sa.Column('flag_key', sa.String(length=255), nullable=False),
        sa.Column('environment_name', sa.String(length=100), nullable=False, server_default='production'),
        sa.Column('root_cause_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'rollback_actions',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('incident_id', GUID(), nullable=True),
        sa.Column('flag_key', sa.String(length=255), nullable=False),
        sa.Column('environment_name', sa.String(length=100), nullable=False, server_default='production'),
        sa.Column('status', sa.Enum('PENDING', 'EXECUTING', 'VERIFIED', 'FAILED', name='rollbackstatus'), nullable=False),
        sa.Column('pre_rollback_state', sa.JSON(), nullable=False),
        sa.Column('target_state', sa.JSON(), nullable=False),
        sa.Column('verified_state', sa.JSON(), nullable=True),
        sa.Column('executed_by', sa.String(length=255), nullable=False, server_default='ReleaseGuardian_Auto'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=255), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. Cleanup Patches
    op.create_table(
        'cleanup_patches',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('organization_id', GUID(), nullable=False),
        sa.Column('repository_id', GUID(), nullable=True),
        sa.Column('flag_key', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('diff_preview', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'REVIEWED', 'PR_CREATED', 'DISMISSED', name='patchstatus'), nullable=False),
        sa.Column('pr_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('cleanup_patches')
    op.drop_table('audit_logs')
    op.drop_table('rollback_actions')
    op.drop_table('incidents')
    op.drop_table('risk_assessments')
    op.drop_table('rollout_policies')
    op.drop_table('telemetry_aggregates')
    op.drop_table('simulation_runs')
    op.drop_table('simulation_scenarios')
    op.drop_table('dependency_edges')
    op.drop_table('flag_references')
    op.drop_table('scans')
    op.drop_table('repositories')
