"""Store encrypted GitHub organization connections and reviewed PR metadata.

Revision ID: 008_github_pr_workflow
Revises: 007_scan_job_idempotency
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008_github_pr_workflow"
down_revision: Union[str, None] = "007_scan_job_idempotency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    id_type = sa.Uuid() if bind.dialect.name == "postgresql" else sa.CHAR(36)
    op.create_table(
        "github_connections",
        sa.Column("organization_id", id_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credential_type", sa.String(32), nullable=False),
        sa.Column("encrypted_token", sa.Text(), nullable=True),
        sa.Column("installation_id", sa.String(64), nullable=True),
        sa.Column("repository_full_name", sa.String(255), nullable=True),
        sa.Column("repository_id", sa.BigInteger(), nullable=True),
        sa.Column("default_branch", sa.String(255), nullable=True),
        sa.Column("id", id_type, primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", name="uq_github_connection_org"),
    )
    op.create_index("ix_github_connections_organization_id", "github_connections", ["organization_id"])
    for name, type_ in (
        ("github_repository_full_name", sa.String(255)),
        ("github_branch", sa.String(255)),
        ("github_base_branch", sa.String(255)),
        ("github_base_commit_sha", sa.String(64)),
        ("github_base_file_sha", sa.String(64)),
        ("github_replacement_encrypted", sa.Text()),
        ("github_commit_sha", sa.String(64)),
        ("github_pr_number", sa.Integer()),
        ("github_pr_state", sa.String(32)),
    ):
        op.add_column("cleanup_patches", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name in (
        "github_pr_state", "github_pr_number", "github_commit_sha",
        "github_replacement_encrypted", "github_base_file_sha",
        "github_base_commit_sha", "github_base_branch", "github_branch",
        "github_repository_full_name",
    ):
        op.drop_column("cleanup_patches", name)
    op.drop_index("ix_github_connections_organization_id", table_name="github_connections")
    op.drop_table("github_connections")
