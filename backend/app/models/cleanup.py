import enum
import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class PatchStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    PR_CREATED = "PR_CREATED"
    DISMISSED = "DISMISSED"


class CleanupPatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cleanup_patches"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True, index=True)
    flag_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    diff_preview: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[PatchStatus] = mapped_column(SQLEnum(PatchStatus), default=PatchStatus.DRAFT, nullable=False)
    pr_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    github_repository_full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_base_branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_base_commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    github_base_file_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    github_replacement_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    github_commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    github_pr_number: Mapped[Optional[int]] = mapped_column(nullable=True)
    github_pr_state: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
