import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.services.dependency_engine import DependencyEngine
from app.api.deps import require_org_member

router = APIRouter()


@router.get("/organizations/{org_id}/graph")
async def get_dependency_graph(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = DependencyEngine(db=db, organization_id=org_id)
    # Ensure inferred edges are populated if any flag references exist
    await engine.build_inferred_graph_from_references()
    return await engine.get_graph()


@router.get("/organizations/{org_id}/graph/blast-radius")
async def get_blast_radius(
    org_id: uuid.UUID,
    flag_key: str,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = DependencyEngine(db=db, organization_id=org_id)
    return await engine.calculate_blast_radius(flag_key)
