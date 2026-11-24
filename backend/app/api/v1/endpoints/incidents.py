import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.incident import Incident, RollbackAction, AuditLog
from app.services.ai_explanation import HybridAIExplanationEngine
from app.api.deps import require_org_member

router = APIRouter()


@router.get("/organizations/{org_id}/incidents")
async def list_incidents(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(Incident).where(Incident.organization_id == org_id).order_by(Incident.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


@router.get("/organizations/{org_id}/rollback-actions")
async def list_rollback_actions(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = (
        select(RollbackAction)
        .where(RollbackAction.organization_id == org_id)
        .order_by(RollbackAction.created_at.desc())
    )
    return (await db.execute(stmt)).scalars().all()


@router.get("/organizations/{org_id}/audit-logs")
async def list_audit_logs(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(AuditLog).where(AuditLog.organization_id == org_id).order_by(AuditLog.created_at.desc())
    return (await db.execute(stmt)).scalars().all()


@router.get("/organizations/{org_id}/incidents/explain")
async def explain_incident(
    org_id: uuid.UUID,
    flag_key: str,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    environment_name: str = "production",
    score: float = 85.0,
):
    return HybridAIExplanationEngine.generate_incident_explanation(
        flag_key=flag_key,
        environment_name=environment_name,
        score=score,
        factors={"affected_services": ["api-service", "web-storefront"], "error_rate": 0.052, "p95_ms": 420.0},
    )
