"""Tie scanner results to durable worker job IDs for restart-safe retries.

Revision ID: 007_scan_job_idempotency
Revises: 006_telemetry_histograms
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "007_scan_job_idempotency"
down_revision: Union[str, None] = "006_telemetry_histograms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    id_type = sa.Uuid() if bind.dialect.name == "postgresql" else sa.CHAR(36)
    op.add_column("scans", sa.Column("background_job_id", id_type, nullable=True))
    op.create_foreign_key("fk_scans_background_job", "scans", "background_jobs", ["background_job_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_scans_background_job_id", "scans", ["background_job_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_scans_background_job_id", table_name="scans")
    op.drop_constraint("fk_scans_background_job", "scans", type_="foreignkey")
    op.drop_column("scans", "background_job_id")
