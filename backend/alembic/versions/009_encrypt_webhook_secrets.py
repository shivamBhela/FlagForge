"""Encrypt previously stored Flagsmith webhook signing secrets.

Revision ID: 009_encrypt_webhook_secrets
Revises: 008_github_pr_workflow
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.crypto import WEBHOOK_SECRET_PREFIX, encrypt_secret


revision: str = "009_encrypt_webhook_secrets"
down_revision: Union[str, None] = "008_github_pr_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "flagsmith_connections",
        "webhook_secret",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=True,
    )
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT id, webhook_secret FROM flagsmith_connections "
        "WHERE webhook_secret IS NOT NULL"
    )).all()
    for row_id, secret in rows:
        if not secret.startswith(WEBHOOK_SECRET_PREFIX):
            bind.execute(
                sa.text("UPDATE flagsmith_connections SET webhook_secret = :secret WHERE id = :id"),
                {"id": row_id, "secret": WEBHOOK_SECRET_PREFIX + encrypt_secret(secret)},
            )


def downgrade() -> None:
    # Keep protected values protected and preserve enough column width.
    pass
