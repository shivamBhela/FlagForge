import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Integer, Float, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class SimulationStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RESTORING = "RESTORING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SimulationScenario(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulation_scenarios"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    environment_name: Mapped[str] = mapped_column(String(100), default="staging", nullable=False)
    target_flag_key: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(50), default="TOGGLE_INVERSION", nullable=False)
    test_traffic_rate: Mapped[int] = mapped_column(Integer, default=100, nullable=False)  # req/s
    duration_seconds: Mapped[int] = mapped_column(Integer, default=15, nullable=False)

    runs: Mapped[List["SimulationRun"]] = relationship("SimulationRun", back_populates="scenario", cascade="all, delete-orphan")


class SimulationRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "simulation_runs"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simulation_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[SimulationStatus] = mapped_column(SQLEnum(SimulationStatus), default=SimulationStatus.PENDING, nullable=False)

    # Initial state snapshot guaranteed to be restored
    pre_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    restored_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Results
    baseline_error_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    simulated_error_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    baseline_p95_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    simulated_p95_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    log_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scenario: Mapped["SimulationScenario"] = relationship("SimulationScenario", back_populates="runs")
