import enum
import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Float, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class NodeType(str, enum.Enum):
    FLAG = "FLAG"
    COMPONENT = "COMPONENT"
    SERVICE = "SERVICE"
    API = "API"


class EdgeType(str, enum.Enum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    MANUAL = "MANUAL"


class DependencyEdge(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dependency_edges"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)

    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[NodeType] = mapped_column(SQLEnum(NodeType, name="nodetype"), nullable=False)

    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    target_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_type: Mapped[NodeType] = mapped_column(SQLEnum(NodeType, name="nodetype"), nullable=False)

    edge_type: Mapped[EdgeType] = mapped_column(SQLEnum(EdgeType), default=EdgeType.INFERRED, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_dep_org_source_target", "organization_id", "source_id", "target_id", unique=True),
    )
