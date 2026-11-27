import uuid
import logging
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.guardian import (
    RolloutPolicy,
    RiskAssessment,
    RiskBand,
    PolicyMode,
)
from app.services.dependency_engine import DependencyEngine
from app.services.telemetry_pipeline import TelemetryPipeline

logger = logging.getLogger("risk-engine")


class DeterministicRiskEngine:
    """Calculates deterministic, auditable risk scores (0-100) using configurable mathematical weights."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def get_or_create_policy(self, project_id: Optional[uuid.UUID] = None) -> RolloutPolicy:
        """Retrieves active policy or seeds default configuration."""
        stmt = select(RolloutPolicy).where(RolloutPolicy.organization_id == self.organization_id)
        if project_id:
            stmt = stmt.where(RolloutPolicy.project_id == project_id)
        policy = (await self.db.execute(stmt)).scalar_one_or_none()

        if not policy:
            policy = RolloutPolicy(
                organization_id=self.organization_id,
                project_id=project_id,
                name="Default Platform Safety Policy",
                mode=PolicyMode.AUTOMATIC,
            )
            self.db.add(policy)
            await self.db.commit()
            await self.db.refresh(policy)

        return policy

    async def evaluate_risk(
        self,
        flag_key: str,
        environment_name: str = "production",
        project_id: Optional[uuid.UUID] = None,
    ) -> RiskAssessment:
        """Evaluates release risk using the deterministic formula:
        risk = 0.30*dependency_impact + 0.25*error_anomaly + 0.20*latency_anomaly + 0.15*change_criticality + 0.10*rollout_velocity
        """
        policy = await self.get_or_create_policy(project_id)

        # 1. Dependency impact component
        dep_engine = DependencyEngine(self.db, self.organization_id)
        blast = await dep_engine.calculate_blast_radius(flag_key)
        dep_impact = float(blast.get("impact_score", 15.0))

        # 2. Telemetry metrics component
        telem_pipe = TelemetryPipeline(self.db, self.organization_id)
        telem = await telem_pipe.get_metrics_for_flag(flag_key, environment_name)

        telemetry_sufficient = (
            telem["has_telemetry"]
            and telem["total_requests"] >= policy.min_telemetry_samples
            and telem.get("has_latency_histogram", False)
            and telem.get("avg_p95_ms") is not None
        )
        if not telemetry_sufficient:
            # Unknown production behavior is not evidence of health. Keep the
            # score deterministic and conservative, and require manual review.
            err_anomaly = 100.0
            lat_anomaly = 100.0
        else:
            # Error rate anomaly: 0% = 0, 5% = 100
            err_anomaly = min(100.0, (telem["avg_error_rate"] / policy.max_error_rate_threshold) * 100.0)
            # Latency anomaly: 100ms = 0, 500ms = 100
            lat_anomaly = min(100.0, max(0.0, (telem["avg_p95_ms"] - 100.0) / (policy.max_p95_latency_ms - 100.0)) * 100.0)

        # 3. Change criticality & rollout velocity
        is_prod = "prod" in environment_name.lower()
        change_criticality = 80.0 if is_prod else 25.0
        rollout_velocity = 50.0  # Moderate default rollout rate

        # Deterministic formula calculation
        score = (
            policy.weight_dependency_impact * dep_impact
            + policy.weight_error_anomaly * err_anomaly
            + policy.weight_latency_anomaly * lat_anomaly
            + policy.weight_change_criticality * change_criticality
            + policy.weight_rollout_velocity * rollout_velocity
        )
        score = round(min(100.0, max(0.0, score)), 2)

        # Determine band
        if score < 30.0:
            band = RiskBand.LOW
            action = "ALLOW_ROLLOUT"
        elif score < 50.0:
            band = RiskBand.MODERATE
            action = "PROCEED_WITH_CANARY"
        elif score < 75.0:
            band = RiskBand.HIGH
            action = "MANUAL_APPROVAL_REQUIRED"
        else:
            band = RiskBand.CRITICAL
            # Rollback is not implemented with provider-side concurrency guarantees.
            # A critical score must remain advisory and require a human decision.
            action = "MANUAL_APPROVAL_REQUIRED"

        if not telemetry_sufficient:
            action = "MANUAL_APPROVAL_REQUIRED"

        assessment = RiskAssessment(
            organization_id=self.organization_id,
            project_id=project_id,
            flag_key=flag_key,
            environment_name=environment_name,
            calculated_score=score,
            risk_band=band,
            dependency_score=round(dep_impact, 2),
            error_anomaly_score=round(err_anomaly, 2),
            latency_anomaly_score=round(lat_anomaly, 2),
            criticality_score=round(change_criticality, 2),
            velocity_score=round(rollout_velocity, 2),
            factors={
                "affected_services": blast.get("affected_services", []),
                "error_rate": telem.get("avg_error_rate", 0.0),
                "p95_ms": telem.get("avg_p95_ms", 0.0),
                "policy_mode": policy.mode.value,
                "telemetry_confidence": "SUFFICIENT" if telemetry_sufficient else "INSUFFICIENT",
                "telemetry_request_count": telem.get("total_requests", 0),
                "telemetry_window_count": telem.get("samples_count", 0),
                "rollback_available": False,
            },
            recommended_action=action,
        )
        self.db.add(assessment)
        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment
