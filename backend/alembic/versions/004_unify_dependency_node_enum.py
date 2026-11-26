"""Unify dependency edge node enum types.

Revision ID: 004_unify_dependency_node_enum
Revises: 003_full_platform_schema
Create Date: 2026-11-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "004_unify_dependency_node_enum"
down_revision: Union[str, None] = "003_full_platform_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NODE_VALUES = ("FLAG", "COMPONENT", "SERVICE", "API")


def upgrade() -> None:
    bind = op.get_bind()
    target_type_name = bind.execute(
        sa.text(
            "SELECT udt_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() "
            "AND table_name = 'dependency_edges' AND column_name = 'target_type'"
        )
    ).scalar_one_or_none()

    if target_type_name == "nodetype_target":
        node_type = postgresql.ENUM(*NODE_VALUES, name="nodetype", create_type=False)
        op.alter_column(
            "dependency_edges",
            "target_type",
            type_=node_type,
            postgresql_using="target_type::text::nodetype",
        )
        op.execute("DROP TYPE nodetype_target")


def downgrade() -> None:
    bind = op.get_bind()
    target_type = postgresql.ENUM(*NODE_VALUES, name="nodetype_target")
    target_type.create(bind, checkfirst=True)
    op.alter_column(
        "dependency_edges",
        "target_type",
        type_=postgresql.ENUM(*NODE_VALUES, name="nodetype_target", create_type=False),
        postgresql_using="target_type::text::nodetype_target",
    )
