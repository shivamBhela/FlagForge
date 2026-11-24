import enum
import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Boolean, Enum as SQLEnum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.environment import Environment


class FeatureFlagType(str, enum.Enum):
    FLAG = "FLAG"
    CONFIG = "CONFIG"
    MULTIVARIATE = "MULTIVARIATE"


class FeatureFlag(Base, TimestampMixin):
    """Synchronized feature flag entity scoped to a project."""
    __tablename__ = "feature_flags"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flagsmith_feature_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[FeatureFlagType] = mapped_column(
        SQLEnum(FeatureFlagType),
        default=FeatureFlagType.FLAG,
        nullable=False,
    )
    default_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped["Project"] = relationship("Project")
    states: Mapped[List["FeatureFlagState"]] = relationship(
        "FeatureFlagState",
        back_populates="feature_flag",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("project_id", "key", name="uq_project_flag_key"),
        Index("ix_flags_project_key", "project_id", "key"),
    )


class FeatureFlagState(Base, TimestampMixin):
    """Environment-specific feature flag activation state and value."""
    __tablename__ = "feature_flag_states"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    feature_flag_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("feature_flags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flagsmith_feature_state_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    feature_flag: Mapped["FeatureFlag"] = relationship("FeatureFlag", back_populates="states")
    environment: Mapped["Environment"] = relationship("Environment")

    __table_args__ = (
        UniqueConstraint("feature_flag_id", "environment_id", name="uq_flag_environment"),
        Index("ix_flag_state_env", "feature_flag_id", "environment_id"),
    )
