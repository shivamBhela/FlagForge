import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Integer, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class TelemetryAggregate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "telemetry_aggregates"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    environment_name: Mapped[str] = mapped_column(String(100), default="production", nullable=False)
    feature_flag_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p50_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p95_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p99_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    __table_args__ = (
        Index("ix_telemetry_org_flag_window", "organization_id", "feature_flag_key", "window_start"),
    )
