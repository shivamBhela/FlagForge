import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Integer, Float, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class ScanStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReferenceStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    STALE = "STALE"
    UNRESOLVED = "UNRESOLVED"


class Repository(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "repositories"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_url: Mapped[str] = mapped_column(String(512), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="typescript", nullable=False)

    scans: Mapped[List["Scan"]] = relationship("Scan", back_populates="repository", cascade="all, delete-orphan")


class Scan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scans"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha: Mapped[str] = mapped_column(String(40), default="HEAD", nullable=False)
    branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    status: Mapped[ScanStatus] = mapped_column(SQLEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    files_scanned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    repository: Mapped["Repository"] = relationship("Repository", back_populates="scans")
    references: Mapped[List["FlagReference"]] = relationship("FlagReference", back_populates="scan", cascade="all, delete-orphan")


class FlagReference(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "flag_references"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    flag_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    symbol_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parser_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    evidence_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ReferenceStatus] = mapped_column(SQLEnum(ReferenceStatus), default=ReferenceStatus.CONFIRMED, nullable=False)

    scan: Mapped["Scan"] = relationship("Scan", back_populates="references")
