import uuid
from typing import Annotated, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.code_intelligence import Repository, Scan, FlagReference
from app.services.scanner import CodeScanner
from app.api.deps import require_org_member, require_org_admin

router = APIRouter()


class RepositoryCreate(BaseModel):
    name: str
    repo_url: str
    default_branch: str = "main"
    language: str = "typescript"
    project_id: Optional[uuid.UUID] = None


class ScanTriggerRequest(BaseModel):
    commit_sha: str = "HEAD"
    branch: str = "main"
    custom_files: Optional[Dict[str, str]] = None


@router.get("/organizations/{org_id}/repositories")
async def list_repositories(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(Repository).where(Repository.organization_id == org_id)
    repos = (await db.execute(stmt)).scalars().all()
    return repos


@router.post("/organizations/{org_id}/repositories", status_code=status.HTTP_201_CREATED)
async def create_repository(
    org_id: uuid.UUID,
    repo_in: RepositoryCreate,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = Repository(
        organization_id=org_id,
        project_id=repo_in.project_id,
        name=repo_in.name,
        repo_url=repo_in.repo_url,
        default_branch=repo_in.default_branch,
        language=repo_in.language,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return repo


@router.post("/organizations/{org_id}/repositories/{repo_id}/scan")
async def trigger_scan(
    org_id: uuid.UUID,
    repo_id: uuid.UUID,
    scan_in: ScanTriggerRequest,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    scanner = CodeScanner(db=db, organization_id=org_id)
    scan = await scanner.execute_scan(
        repository_id=repo_id,
        commit_sha=scan_in.commit_sha,
        branch=scan_in.branch,
        custom_files=scan_in.custom_files,
    )
    return scan


@router.get("/organizations/{org_id}/scans")
async def list_scans(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(Scan).where(Scan.organization_id == org_id).order_by(Scan.created_at.desc())
    scans = (await db.execute(stmt)).scalars().all()
    return scans


@router.get("/organizations/{org_id}/flag-references")
async def list_flag_references(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    flag_key: Optional[str] = None,
):
    stmt = select(FlagReference).where(FlagReference.organization_id == org_id)
    if flag_key:
        stmt = stmt.where(FlagReference.flag_key == flag_key)
    refs = (await db.execute(stmt.order_by(FlagReference.created_at.desc()))).scalars().all()
    return refs
