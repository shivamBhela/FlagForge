"""Add tenant-scoped Redis worker job status records.

Revision ID: 005_background_jobs
Revises: 004_unify_dependency_node_enum
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_background_jobs"
down_revision: Union[str, None] = "004_unify_dependency_node_enum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    id_type = postgresql.UUID(as_uuid=True) if bind.dialect.name == "postgresql" else sa.CHAR(36)
    op.create_table(
        "background_jobs",
        sa.Column("id", id_type, primary_key=True, nullable=False),
        sa.Column("organization_id", id_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_background_jobs_organization_id", "background_jobs", ["organization_id"])
    op.create_index("ix_background_jobs_status", "background_jobs", ["status"])
    op.create_index("ix_background_job_org_created", "background_jobs", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_background_job_org_created", table_name="background_jobs")
    op.drop_index("ix_background_jobs_status", table_name="background_jobs")
    op.drop_index("ix_background_jobs_organization_id", table_name="background_jobs")
    op.drop_table("background_jobs")
