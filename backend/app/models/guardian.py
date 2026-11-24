import enum
import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Integer, Float, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class PolicyMode(str, enum.Enum):
    MONITOR = "MONITOR"
    NOTIFY = "NOTIFY"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    AUTOMATIC = "AUTOMATIC"


class RiskBand(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class RolloutPolicy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rollout_policies"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="Default Rollout Policy", nullable=False)
    mode: Mapped[PolicyMode] = mapped_column(SQLEnum(PolicyMode), default=PolicyMode.AUTOMATIC, nullable=False)

    # Weights for deterministic calculation
    weight_dependency_impact: Mapped[float] = mapped_column(Float, default=0.30, nullable=False)
    weight_error_anomaly: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    weight_latency_anomaly: Mapped[float] = mapped_column(Float, default=0.20, nullable=False)
    weight_change_criticality: Mapped[float] = mapped_column(Float, default=0.15, nullable=False)
    weight_rollout_velocity: Mapped[float] = mapped_column(Float, default=0.10, nullable=False)

    # Safety thresholds
    max_error_rate_threshold: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)  # 5%
    max_p95_latency_ms: Mapped[float] = mapped_column(Float, default=500.0, nullable=False)
    critical_risk_threshold: Mapped[float] = mapped_column(Float, default=75.0, nullable=False)
    min_telemetry_samples: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    kill_switch_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)


class RiskAssessment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "risk_assessments"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    flag_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    environment_name: Mapped[str] = mapped_column(String(100), default="production", nullable=False)

    calculated_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_band: Mapped[RiskBand] = mapped_column(SQLEnum(RiskBand), default=RiskBand.LOW, nullable=False)

    dependency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_anomaly_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_anomaly_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    criticality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    velocity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    factors: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(100), default="ALLOW_ROLLOUT", nullable=False)
