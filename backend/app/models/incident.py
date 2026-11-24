import enum
import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    ROLLED_BACK = "ROLLED_BACK"
    RESOLVED = "RESOLVED"


class RollbackStatus(str, enum.Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class Incident(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incidents"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[IncidentSeverity] = mapped_column(SQLEnum(IncidentSeverity), default=IncidentSeverity.HIGH, nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(SQLEnum(IncidentStatus), default=IncidentStatus.DETECTED, nullable=False)
    flag_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    environment_name: Mapped[str] = mapped_column(String(100), default="production", nullable=False)
    root_cause_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RollbackAction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rollback_actions"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    flag_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    environment_name: Mapped[str] = mapped_column(String(100), default="production", nullable=False)
    status: Mapped[RollbackStatus] = mapped_column(SQLEnum(RollbackStatus), default=RollbackStatus.PENDING, nullable=False)

    pre_rollback_state: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    target_state: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    verified_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    executed_by: Mapped[str] = mapped_column(String(255), default="ReleaseGuardian_Auto", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
