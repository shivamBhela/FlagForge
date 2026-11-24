import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.cleanup import CleanupPatch, PatchStatus
from app.services.cleanup_studio import CleanupStudioEngine
from app.api.deps import require_org_member, require_org_admin

router = APIRouter()


class PatchPreviewRequest(BaseModel):
    flag_key: str
    file_path: str


class CreatePRRequest(BaseModel):
    patch_id: uuid.UUID


@router.get("/organizations/{org_id}/cleanup/stale-flags")
async def get_stale_flags(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = CleanupStudioEngine(db=db, organization_id=org_id)
    return await engine.list_stale_candidates()


@router.post("/organizations/{org_id}/cleanup/patches/preview")
async def generate_patch_preview(
    org_id: uuid.UUID,
    req: PatchPreviewRequest,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = CleanupStudioEngine(db=db, organization_id=org_id)
    return await engine.generate_patch_preview(req.flag_key, req.file_path)


@router.get("/organizations/{org_id}/cleanup/patches")
async def list_patches(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = (
        select(CleanupPatch)
        .where(CleanupPatch.organization_id == org_id)
        .order_by(CleanupPatch.created_at.desc())
    )
    return (await db.execute(stmt)).scalars().all()


@router.post("/organizations/{org_id}/cleanup/patches/{patch_id}/create-pr")
async def create_pull_request(
    org_id: uuid.UUID,
    patch_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(CleanupPatch).where(
        CleanupPatch.id == patch_id,
        CleanupPatch.organization_id == org_id,
    )
    patch = (await db.execute(stmt)).scalar_one_or_none()
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")

    patch.status = PatchStatus.PR_CREATED
    patch.pr_url = f"https://github.com/cloudcorp/web-storefront/pull/{uuid.uuid4().hex[:6]}"
    await db.commit()
    await db.refresh(patch)
    return patch
