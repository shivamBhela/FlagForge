import uuid
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_org_admin, require_org_member
from app.core.config import settings
from app.core.crypto import encrypt_secret
from app.core.database import get_db
from app.models.github import GitHubConnection
from app.models.organization import OrganizationMember
from app.services.github_client import GitHubApiError, GitHubClient, get_client_for_connection

router = APIRouter()


class GitHubConnectRequest(BaseModel):
    credential_type: Literal["FINE_GRAINED_PAT", "APP_INSTALLATION"]
    token: Optional[str] = Field(default=None, min_length=20, max_length=500)
    installation_id: Optional[str] = Field(default=None, min_length=1, max_length=64)


class GitHubRepositorySelection(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)


def map_github_error(exc: GitHubApiError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


async def get_github_connection(db: AsyncSession, org_id: uuid.UUID) -> GitHubConnection:
    row = (await db.execute(select(GitHubConnection).where(GitHubConnection.organization_id == org_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="GitHub integration is not configured for this organization.")
    return row


@router.get("/organizations/{org_id}/github/connection")
async def get_connection(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(select(GitHubConnection).where(GitHubConnection.organization_id == org_id))).scalar_one_or_none()
    if not row:
        return {"connected": False, "github_app_available": bool(settings.GITHUB_APP_ID and settings.GITHUB_APP_PRIVATE_KEY)}
    return {
        "connected": True,
        "credential_type": row.credential_type,
        "has_token": bool(row.encrypted_token) or row.credential_type == "APP_INSTALLATION",
        "repository_full_name": row.repository_full_name,
        "default_branch": row.default_branch,
        "github_app_available": bool(settings.GITHUB_APP_ID and settings.GITHUB_APP_PRIVATE_KEY),
    }


@router.put("/organizations/{org_id}/github/connection")
async def save_connection(
    org_id: uuid.UUID,
    body: GitHubConnectRequest,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(select(GitHubConnection).where(GitHubConnection.organization_id == org_id))).scalar_one_or_none()
    if body.credential_type == "APP_INSTALLATION":
        if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
            raise HTTPException(status_code=503, detail="Configure the GitHub App ID and private key on the server first.")
        if not body.installation_id:
            raise HTTPException(status_code=422, detail="An installed GitHub App installation ID is required.")
        new_row = GitHubConnection(
            organization_id=org_id,
            credential_type=body.credential_type,
            installation_id=body.installation_id,
        )
        try:
            client = await get_client_for_connection(new_row)
            await client.list_repositories("APP_INSTALLATION")
        except GitHubApiError as exc:
            raise map_github_error(exc)
    else:
        if not body.token:
            raise HTTPException(status_code=422, detail="A fine-grained GitHub token is required.")
        client = GitHubClient(body.token)
        try:
            await client.list_repositories("FINE_GRAINED_PAT")
        except GitHubApiError as exc:
            raise map_github_error(exc)
        new_row = GitHubConnection(
            organization_id=org_id,
            credential_type=body.credential_type,
            encrypted_token=encrypt_secret(body.token),
        )

    if row:
        row.credential_type = new_row.credential_type
        row.encrypted_token = new_row.encrypted_token
        row.installation_id = new_row.installation_id
        row.repository_full_name = None
        row.repository_id = None
        row.default_branch = None
    else:
        db.add(new_row)
    await db.commit()
    return {"connected": True, "credential_type": new_row.credential_type if not row else row.credential_type, "has_token": True}


@router.get("/organizations/{org_id}/github/repositories")
async def list_repositories(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await get_github_connection(db, org_id)
    try:
        client = await get_client_for_connection(row)
        return await client.list_repositories(row.credential_type)
    except GitHubApiError as exc:
        raise map_github_error(exc)


@router.put("/organizations/{org_id}/github/repository")
async def select_repository(
    org_id: uuid.UUID,
    body: GitHubRepositorySelection,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await get_github_connection(db, org_id)
    try:
        client = await get_client_for_connection(row)
        authorized = await client.list_repositories(row.credential_type)
        selected = next((repo for repo in authorized if repo["full_name"].lower() == body.full_name.lower()), None)
        if not selected:
            raise HTTPException(status_code=403, detail="Repository is not authorized by this GitHub connection.")
        repo = await client.get_repository(selected["full_name"])
    except GitHubApiError as exc:
        raise map_github_error(exc)
    row.repository_full_name = repo["full_name"]
    row.repository_id = repo.get("id")
    row.default_branch = repo.get("default_branch")
    await db.commit()
    return {"repository_full_name": row.repository_full_name, "default_branch": row.default_branch, "private": bool(repo.get("private"))}


@router.delete("/organizations/{org_id}/github/connection", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await get_github_connection(db, org_id)
    await db.delete(row)
    await db.commit()
