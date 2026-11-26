"""Retain OTLP histogram distributions for correct percentile aggregation.

Revision ID: 006_telemetry_histograms
Revises: 005_background_jobs
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006_telemetry_histograms"
down_revision: Union[str, None] = "005_background_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    id_type = sa.Uuid() if bind.dialect.name == "postgresql" else sa.CHAR(36)
    op.add_column("telemetry_aggregates", sa.Column("project_id", id_type, nullable=True))
    op.create_foreign_key("fk_telemetry_project", "telemetry_aggregates", "projects", ["project_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_telemetry_aggregates_project_id", "telemetry_aggregates", ["project_id"])
    op.add_column("telemetry_aggregates", sa.Column("latency_bucket_bounds", sa.JSON(), nullable=True))
    op.add_column("telemetry_aggregates", sa.Column("latency_bucket_counts", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("telemetry_aggregates", "latency_bucket_counts")
    op.drop_column("telemetry_aggregates", "latency_bucket_bounds")
    op.drop_index("ix_telemetry_aggregates_project_id", table_name="telemetry_aggregates")
    op.drop_constraint("fk_telemetry_project", "telemetry_aggregates", type_="foreignkey")
    op.drop_column("telemetry_aggregates", "project_id")
