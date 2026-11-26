import uuid
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class GitHubConnection(Base, UUIDMixin, TimestampMixin):
    """Organization-scoped GitHub credentials and selected repository."""

    __tablename__ = "github_connections"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    credential_type: Mapped[str] = mapped_column(String(32), nullable=False)
    encrypted_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    installation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    repository_full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    repository_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    default_branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (UniqueConstraint("organization_id", name="uq_github_connection_org"),)
