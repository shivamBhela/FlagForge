import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Integer, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, GUID, utc_now

if TYPE_CHECKING:
    from app.models.organization import Organization


class FlagsmithConnectionType(str, enum.Enum):
    CLOUD = "CLOUD"
    SELF_HOSTED = "SELF_HOSTED"


class FlagsmithConnectionStatus(str, enum.Enum):
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class SyncStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SyncTrigger(str, enum.Enum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    WEBHOOK = "WEBHOOK"


class WebhookStatus(str, enum.Enum):
    PROCESSED = "PROCESSED"
    IGNORED = "IGNORED"
    FAILED = "FAILED"


class FlagsmithConnection(Base, TimestampMixin):
    """Encrypted connection configuration to a Flagsmith Cloud or self-hosted instance."""
    __tablename__ = "flagsmith_connections"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_url: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)
    connection_type: Mapped[FlagsmithConnectionType] = mapped_column(
        SQLEnum(FlagsmithConnectionType),
        default=FlagsmithConnectionType.CLOUD,
        nullable=False,
    )
    status: Mapped[FlagsmithConnectionStatus] = mapped_column(
        SQLEnum(FlagsmithConnectionStatus),
        default=FlagsmithConnectionStatus.DISCONNECTED,
        nullable=False,
    )
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    sync_histories: Mapped[List["SyncHistory"]] = relationship(
        "SyncHistory",
        back_populates="connection",
        cascade="all, delete-orphan",
    )
    webhook_events: Mapped[List["WebhookEvent"]] = relationship(
        "WebhookEvent",
        back_populates="connection",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_flagsmith_org_status", "organization_id", "status"),
    )


class SyncHistory(Base, TimestampMixin):
    """Audit record of feature flag synchronization runs."""
    __tablename__ = "sync_histories"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("flagsmith_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[SyncStatus] = mapped_column(
        SQLEnum(SyncStatus),
        default=SyncStatus.PENDING,
        nullable=False,
    )
    trigger: Mapped[SyncTrigger] = mapped_column(
        SQLEnum(SyncTrigger),
        default=SyncTrigger.MANUAL,
        nullable=False,
    )
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_unchanged: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    connection: Mapped["FlagsmithConnection"] = relationship("FlagsmithConnection", back_populates="sync_histories")


class WebhookEvent(Base, TimestampMixin):
    """Audit log of received Flagsmith webhook events."""
    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("flagsmith_connections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    signature: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[WebhookStatus] = mapped_column(
        SQLEnum(WebhookStatus),
        default=WebhookStatus.PROCESSED,
        nullable=False,
    )

    connection: Mapped[Optional["FlagsmithConnection"]] = relationship(
        "FlagsmithConnection",
        back_populates="webhook_events",
    )
