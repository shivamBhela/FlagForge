import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, GUID, TimestampMixin


class BackgroundJob(Base, TimestampMixin):
    """Tenant-scoped durable status record for Redis Stream jobs."""
    __tablename__ = "background_jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_background_job_org_created", "organization_id", "created_at"),)
