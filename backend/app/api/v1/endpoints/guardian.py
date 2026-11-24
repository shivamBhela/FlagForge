import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.guardian import RolloutPolicy, PolicyMode, RiskAssessment
from app.services.risk_engine import DeterministicRiskEngine
from app.services.release_guardian import ReleaseGuardianEngine
from app.api.deps import require_org_member, require_org_admin

router = APIRouter()


class PolicyUpdate(BaseModel):
    mode: Optional[PolicyMode] = None
    weight_dependency_impact: Optional[float] = None
    weight_error_anomaly: Optional[float] = None
    weight_latency_anomaly: Optional[float] = None
    weight_change_criticality: Optional[float] = None
    weight_rollout_velocity: Optional[float] = None
    max_error_rate_threshold: Optional[float] = None
    max_p95_latency_ms: Optional[float] = None
    critical_risk_threshold: Optional[float] = None
    kill_switch_enabled: Optional[bool] = None


class RollbackRequest(BaseModel):
    flag_key: str
    environment_name: str = "production"
    reason: str = "Manual trigger or safety threshold exceeded"


@router.get("/organizations/{org_id}/policy")
async def get_policy(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = DeterministicRiskEngine(db=db, organization_id=org_id)
    return await engine.get_or_create_policy()


@router.put("/organizations/{org_id}/policy")
async def update_policy(
    org_id: uuid.UUID,
    policy_in: PolicyUpdate,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = DeterministicRiskEngine(db=db, organization_id=org_id)
    policy = await engine.get_or_create_policy()

    for k, v in policy_in.model_dump(exclude_unset=True).items():
        setattr(policy, k, v)

    await db.commit()
    await db.refresh(policy)
    return policy


@router.post("/organizations/{org_id}/guardian/evaluate")
async def evaluate_risk(
    org_id: uuid.UUID,
    flag_key: str,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    environment_name: str = "production",
):
    engine = DeterministicRiskEngine(db=db, organization_id=org_id)
    return await engine.evaluate_risk(flag_key=flag_key, environment_name=environment_name)


@router.post("/organizations/{org_id}/guardian/rollback")
async def execute_rollback(
    org_id: uuid.UUID,
    req: RollbackRequest,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = ReleaseGuardianEngine(db=db, organization_id=org_id)
    try:
        action = await engine.execute_verified_rollback(
            flag_key=req.flag_key,
            environment_name=req.environment_name,
            reason=req.reason,
            executed_by=membership.user.email if membership.user else "AdminUser",
        )
        return action
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
