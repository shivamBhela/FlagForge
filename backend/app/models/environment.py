import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.project import Project


class Environment(Base, TimestampMixin):
    """Environment entity (Production, Staging, Dev) scoped to a Project."""
    __tablename__ = "environments"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    is_production: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    flagsmith_environment_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="environments",
    )

    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_project_env_slug"),
        Index("ix_envs_project_slug", "project_id", "slug"),
    )
