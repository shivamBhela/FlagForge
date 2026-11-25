import uuid
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.guardian import RolloutPolicy
from app.models.incident import RollbackAction, RollbackStatus
from app.models.feature_flag import FeatureFlag, FeatureFlagState


class ReleaseGuardianEngine:
    """Enforces safety pre-conditions, policy validation, and verified atomic rollbacks."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def check_preconditions(self, flag_key: str, environment_name: str) -> Tuple[bool, str]:
        """Validates all required preconditions before executing any rollback mutation."""
        stmt_pol = select(RolloutPolicy).where(RolloutPolicy.organization_id == self.organization_id)
        policy = (await self.db.execute(stmt_pol)).scalar_one_or_none()

        if policy and not policy.kill_switch_enabled:
            return False, "Automation kill switch is engaged across this organization."

        stmt_flag = (
            select(FeatureFlag)
            .where(
                FeatureFlag.key == flag_key,
                FeatureFlag.project.has(organization_id=self.organization_id),
            )
            .order_by(FeatureFlag.created_at)
            .limit(1)
        )
        flag = (await self.db.execute(stmt_flag)).scalar_one_or_none()
        if not flag:
            # Check if referenced in code scan
            from app.models.code_intelligence import FlagReference
            stmt_ref = (
                select(FlagReference)
                .where(
                    FlagReference.organization_id == self.organization_id,
                    FlagReference.flag_key == flag_key,
                )
                .order_by(FlagReference.created_at)
                .limit(1)
            )
            ref = (await self.db.execute(stmt_ref)).scalar_one_or_none()
            if not ref:
                return False, f"Flag '{flag_key}' not found in registry."

        # 3. Concurrency Protection: Prevent duplicate active rollback executions
        stmt_active = select(RollbackAction).where(
            RollbackAction.organization_id == self.organization_id,
            RollbackAction.flag_key == flag_key,
            RollbackAction.environment_name == environment_name,
            RollbackAction.status == RollbackStatus.EXECUTING,
        )
        active_rb = (await self.db.execute(stmt_active)).scalar_one_or_none()
        if active_rb:
            return False, f"Rollback action for flag '{flag_key}' is already executing (concurrency protection)."

        return True, "All preconditions verified."

    async def execute_verified_rollback(
        self,
        flag_key: str,
        environment_name: str = "production",
        reason: str = "Critical anomaly threshold breached",
        executed_by: str = "ReleaseGuardian_Auto",
    ) -> RollbackAction:
        """Refuse a rollback until remote mutation and read-after-write are implemented."""
        allowed, msg = await self.check_preconditions(flag_key, environment_name)
        if not allowed:
            raise PermissionError(f"Rollback refused: {msg}")
        raise NotImplementedError(
            "Remote Flagsmith rollback is disabled until a provider write and read-after-write verification are implemented. No change was made."
        )
