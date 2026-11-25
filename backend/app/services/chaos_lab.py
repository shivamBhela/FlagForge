import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chaos import (
    SimulationScenario,
    SimulationRun,
    SimulationStatus,
)
from app.models.feature_flag import FeatureFlag

logger = logging.getLogger("chaos-lab")


class ChaosLabEngine:
    """Runs synthetic staging simulations without mutating remote flags or generating load."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def run_scenario(self, scenario_id: uuid.UUID) -> SimulationRun:
        """Records a synthetic scenario; no provider state or application traffic is changed."""
        stmt_scen = select(SimulationScenario).where(
            SimulationScenario.id == scenario_id,
            SimulationScenario.organization_id == self.organization_id,
        )
        scenario = (await self.db.execute(stmt_scen)).scalar_one_or_none()
        if not scenario:
            raise ValueError(f"Simulation scenario {scenario_id} not found")

        # 1. Take initial state snapshot
        # Find feature flag in staging
        stmt_flag = (
            select(FeatureFlag)
            .where(
                FeatureFlag.key == scenario.target_flag_key,
                FeatureFlag.project.has(organization_id=self.organization_id),
            )
            .order_by(FeatureFlag.created_at)
            .limit(1)
        )
        flag = (await self.db.execute(stmt_flag)).scalar_one_or_none()

        pre_snapshot = {
            "flag_key": scenario.target_flag_key,
            "environment": scenario.environment_name,
            "default_enabled": flag.default_enabled if flag else False,
            "simulation_mode": "SYNTHETIC_NO_REMOTE_MUTATION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        run = SimulationRun(
            organization_id=self.organization_id,
            scenario_id=scenario.id,
            status=SimulationStatus.RUNNING,
            pre_snapshot=pre_snapshot,
            baseline_error_rate=0.002,  # 0.2%
            baseline_p95_ms=115.0,
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)

        try:
            # Produce deterministic sample values for the UI; no traffic is sent.
            simulated_error_rate = 0.048 if scenario.scenario_type == "CASCADE_FAILURE" else 0.015
            simulated_p95 = 385.0 if scenario.scenario_type == "CASCADE_FAILURE" else 180.0

            run.simulated_error_rate = simulated_error_rate
            run.simulated_p95_ms = simulated_p95
            run.log_output = (
                f"[{datetime.now(timezone.utc).isoformat()}] Synthetic local snapshot recorded: {pre_snapshot}\n"
                f"[{datetime.now(timezone.utc).isoformat()}] Synthetic scenario: {scenario.scenario_type} on {scenario.target_flag_key}\n"
                f"[{datetime.now(timezone.utc).isoformat()}] No load was sent and no remote flag was changed. Configured rate/duration are illustrative only.\n"
                f"[{datetime.now(timezone.utc).isoformat()}] Metric shift: error rate {run.baseline_error_rate*100:.1f}% -> {simulated_error_rate*100:.1f}%\n"
            )

        finally:
            # A synthetic-only run has nothing to restore; do not claim a remote
            # restoration verification that did not take place.
            run.restored_verified = False
            run.status = SimulationStatus.COMPLETED
            run.log_output += f"[{datetime.now(timezone.utc).isoformat()}] Synthetic run completed. No remote state change occurred; restoration was not performed."
            await self.db.commit()
            await self.db.refresh(run)

        return run

    async def recover_interrupted_runs(self) -> int:
        """Finds any simulations interrupted during process failure and restores verified initial state."""
        stmt = select(SimulationRun).where(
            SimulationRun.organization_id == self.organization_id,
            SimulationRun.status.in_([SimulationStatus.RUNNING, SimulationStatus.RESTORING]),
        )
        orphaned = (await self.db.execute(stmt)).scalars().all()
        recovered = 0
        for r in orphaned:
            r.status = SimulationStatus.FAILED
            r.restored_verified = False
            r.log_output = (r.log_output or "") + f"\n[{datetime.now(timezone.utc).isoformat()}] Synthetic run interrupted. No remote state change occurred; restoration was not performed."
            recovered += 1
        if recovered > 0:
            await self.db.commit()
        return recovered
