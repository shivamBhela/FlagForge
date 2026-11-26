import difflib
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_org_admin, require_org_member
from app.api.v1.endpoints.github import get_github_connection, map_github_error
from app.core.crypto import decrypt_secret, encrypt_secret
from app.core.database import get_db
from app.models.cleanup import CleanupPatch, PatchStatus
from app.models.code_intelligence import Repository
from app.models.github import GitHubConnection
from app.models.incident import AuditLog
from app.models.organization import OrganizationMember
from app.services.cleanup_studio import CleanupStudioEngine
from app.services.github_client import GitHubApiError, get_client_for_connection

router = APIRouter()


class PatchPreviewRequest(BaseModel):
    flag_key: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1, max_length=1024)
    repository_id: Optional[uuid.UUID] = None


class PrepareGitHubPatchRequest(BaseModel):
    base_file_sha: str = Field(min_length=40, max_length=64)
    base_commit_sha: str = Field(min_length=40, max_length=64)
    replacement_content: str = Field(max_length=1_000_000)


class CreatePRApproval(BaseModel):
    approved: bool


def _safe_path(path: str) -> str:
    if path.startswith("/") or "\\" in path or "\x00" in path or any(p in ("", ".", "..") for p in path.split("/")):
        raise HTTPException(status_code=422, detail="Source path must be a normalized repository-relative path.")
    return path


def _patch_out(patch: CleanupPatch) -> dict:
    return {
        "id": str(patch.id),
        "organization_id": str(patch.organization_id),
        "repository_id": str(patch.repository_id) if patch.repository_id else None,
        "flag_key": patch.flag_key,
        "file_path": patch.file_path,
        "rationale": patch.rationale,
        "diff_preview": patch.diff_preview,
        "status": patch.status.value if hasattr(patch.status, "value") else patch.status,
        "pr_url": patch.pr_url,
        "github_repository_full_name": patch.github_repository_full_name,
        "github_branch": patch.github_branch,
        "github_base_branch": patch.github_base_branch,
        "github_commit_sha": patch.github_commit_sha,
        "github_pr_number": patch.github_pr_number,
        "github_pr_state": patch.github_pr_state,
    }


async def _patch_for_org(db: AsyncSession, org_id: uuid.UUID, patch_id: uuid.UUID) -> CleanupPatch:
    patch = (await db.execute(select(CleanupPatch).where(
        CleanupPatch.id == patch_id,
        CleanupPatch.organization_id == org_id,
    ))).scalar_one_or_none()
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    return patch


async def _selected_github(db: AsyncSession, org_id: uuid.UUID) -> tuple[GitHubConnection, object]:
    connection = await get_github_connection(db, org_id)
    if not connection.repository_full_name or not connection.default_branch:
        raise HTTPException(status_code=409, detail="Select an authorized GitHub repository before preparing a PR.")
    try:
        client = await get_client_for_connection(connection)
    except GitHubApiError as exc:
        raise map_github_error(exc)
    return connection, client


@router.get("/organizations/{org_id}/cleanup/stale-flags")
async def get_stale_flags(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await CleanupStudioEngine(db=db, organization_id=org_id).list_stale_candidates()


@router.post("/organizations/{org_id}/cleanup/patches/preview")
async def generate_patch_preview(
    org_id: uuid.UUID,
    req: PatchPreviewRequest,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    path = _safe_path(req.file_path)
    if req.repository_id:
        repository = (await db.execute(select(Repository).where(
            Repository.id == req.repository_id,
            Repository.organization_id == org_id,
        ))).scalar_one_or_none()
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found in this organization.")
    patch = CleanupPatch(
        organization_id=org_id,
        repository_id=req.repository_id,
        flag_key=req.flag_key,
        file_path=path,
        rationale="Review the actual repository file and propose a specific cleanup. Nothing is changed until you approve a PR.",
        diff_preview="Connect GitHub, select the authorized repository, load this exact file, and prepare a reviewable diff.",
        status=PatchStatus.DRAFT,
    )
    db.add(patch)
    await db.commit()
    await db.refresh(patch)
    return _patch_out(patch)


@router.get("/organizations/{org_id}/cleanup/patches")
async def list_patches(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    patches = (await db.execute(select(CleanupPatch).where(
        CleanupPatch.organization_id == org_id,
    ).order_by(CleanupPatch.created_at.desc()))).scalars().all()
    return [_patch_out(patch) for patch in patches]


@router.get("/organizations/{org_id}/cleanup/patches/{patch_id}/github-source")
async def get_github_source(
    org_id: uuid.UUID,
    patch_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    patch = await _patch_for_org(db, org_id, patch_id)
    connection, client = await _selected_github(db, org_id)
    try:
        base_commit_sha = await client.get_ref(connection.repository_full_name, connection.default_branch)
        content, base_file_sha = await client.get_file(connection.repository_full_name, _safe_path(patch.file_path), base_commit_sha)
    except GitHubApiError as exc:
        raise map_github_error(exc)
    return {
        "repository_full_name": connection.repository_full_name,
        "base_branch": connection.default_branch,
        "base_commit_sha": base_commit_sha,
        "base_file_sha": base_file_sha,
        "file_path": patch.file_path,
        "content": content,
    }


@router.put("/organizations/{org_id}/cleanup/patches/{patch_id}/github-preview")
async def prepare_github_patch(
    org_id: uuid.UUID,
    patch_id: uuid.UUID,
    body: PrepareGitHubPatchRequest,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    patch = await _patch_for_org(db, org_id, patch_id)
    if patch.status == PatchStatus.PR_CREATED or patch.status == PatchStatus.DISMISSED:
        raise HTTPException(status_code=409, detail="This patch can no longer be changed.")
    if not body.replacement_content.strip():
        raise HTTPException(status_code=422, detail="A cleanup patch cannot delete the entire source file.")
    connection, client = await _selected_github(db, org_id)
    try:
        latest_commit = await client.get_ref(connection.repository_full_name, connection.default_branch)
        if latest_commit != body.base_commit_sha:
            raise HTTPException(status_code=409, detail="The default branch changed. Reload the file before preparing this patch.")
        original, latest_file_sha = await client.get_file(connection.repository_full_name, _safe_path(patch.file_path), latest_commit)
    except GitHubApiError as exc:
        raise map_github_error(exc)
    if latest_file_sha != body.base_file_sha:
        raise HTTPException(status_code=409, detail="The source file changed. Reload it before preparing this patch.")
    if original == body.replacement_content:
        raise HTTPException(status_code=422, detail="The proposed file has no changes.")

    diff = "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        body.replacement_content.splitlines(keepends=True),
        fromfile=f"a/{patch.file_path}",
        tofile=f"b/{patch.file_path}",
    ))
    patch.github_repository_full_name = connection.repository_full_name
    patch.github_base_branch = connection.default_branch
    patch.github_base_commit_sha = latest_commit
    patch.github_base_file_sha = latest_file_sha
    patch.github_replacement_encrypted = encrypt_secret(body.replacement_content)
    patch.diff_preview = diff
    patch.status = PatchStatus.DRAFT
    await db.commit()
    await db.refresh(patch)
    return _patch_out(patch)


@router.post("/organizations/{org_id}/cleanup/patches/{patch_id}/create-pr")
async def create_pull_request(
    org_id: uuid.UUID,
    patch_id: uuid.UUID,
    approval: CreatePRApproval,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    patch = await _patch_for_org(db, org_id, patch_id)
    if not approval.approved:
        raise HTTPException(status_code=400, detail="Explicit administrator approval is required to create a GitHub PR.")
    if patch.status == PatchStatus.PR_CREATED and patch.pr_url:
        return _patch_out(patch)
    if not patch.github_replacement_encrypted or not patch.github_base_commit_sha or not patch.github_base_file_sha:
        raise HTTPException(status_code=409, detail="Prepare and review a real GitHub file diff before approving PR creation.")

    connection, client = await _selected_github(db, org_id)
    if connection.repository_full_name != patch.github_repository_full_name or connection.default_branch != patch.github_base_branch:
        raise HTTPException(status_code=409, detail="Selected GitHub repository or base branch changed. Prepare the diff again.")

    try:
        existing = await client.find_pull_request(connection.repository_full_name, f"flagforge/cleanup-{patch.id}", connection.default_branch)
        if existing:
            patch.pr_url = existing.get("html_url")
            patch.github_pr_number = existing.get("number")
            patch.github_pr_state = existing.get("state")
            patch.github_branch = f"flagforge/cleanup-{patch.id}"
            patch.status = PatchStatus.PR_CREATED
            await db.commit()
            return _patch_out(patch)

        replacement = decrypt_secret(patch.github_replacement_encrypted)
        latest_base = await client.get_ref(connection.repository_full_name, connection.default_branch)
        if latest_base != patch.github_base_commit_sha:
            raise HTTPException(status_code=409, detail="The repository default branch advanced. Review a new diff before creating the PR.")
        original, current_blob_sha = await client.get_file(connection.repository_full_name, patch.file_path, latest_base)
        if current_blob_sha != patch.github_base_file_sha:
            raise HTTPException(status_code=409, detail="The source file changed. Review a new diff before creating the PR.")

        patch.status = PatchStatus.REVIEWED
        await db.commit()

        branch = f"flagforge/cleanup-{patch.id}"
        try:
            await client.create_branch(connection.repository_full_name, branch, patch.github_base_commit_sha)
        except GitHubApiError as exc:
            if exc.status_code not in (409, 422):
                raise
            branch_sha = await client.get_ref(connection.repository_full_name, branch)
            if branch_sha != patch.github_base_commit_sha:
                commit = await client.get_commit(connection.repository_full_name, branch_sha)
                parents = {parent.get("sha") for parent in commit.get("parents", [])}
                branch_content, _ = await client.get_file(connection.repository_full_name, patch.file_path, branch_sha)
                if patch.github_base_commit_sha not in parents or branch_content != replacement:
                    raise HTTPException(status_code=409, detail="The deterministic cleanup branch exists with unexpected changes; refusing to overwrite it.")
                patch.github_commit_sha = branch_sha

        if not patch.github_commit_sha:
            result = await client.put_file(
                connection.repository_full_name,
                patch.file_path,
                branch,
                replacement,
                patch.github_base_file_sha,
                f"Prepare reviewed cleanup for {patch.flag_key}",
            )
            patch.github_commit_sha = result.get("commit", {}).get("sha")
        if not patch.github_commit_sha:
            raise GitHubApiError("GitHub did not return a commit for the reviewed file change.")

        pr = await client.create_pull_request(
            connection.repository_full_name,
            branch,
            connection.default_branch,
            f"Remove stale feature flag {patch.flag_key}",
            f"Reviewed FlagForge cleanup proposal for `{patch.flag_key}` in `{patch.file_path}`.\n\n{patch.rationale}\n\nThis PR contains only the reviewed file change. It is not merged automatically.",
        )
    except GitHubApiError as exc:
        raise map_github_error(exc)

    patch.github_branch = branch
    patch.github_pr_number = pr.get("number")
    patch.github_pr_state = pr.get("state")
    patch.pr_url = pr.get("html_url")
    patch.status = PatchStatus.PR_CREATED
    db.add(AuditLog(
        organization_id=org_id,
        action="GITHUB_CLEANUP_PR_CREATED",
        actor=membership.user.email if membership.user else "Organization admin",
        resource_type="cleanup_patch",
        resource_id=str(patch.id),
        details={"repository": connection.repository_full_name, "branch": branch, "pr_number": patch.github_pr_number},
    ))
    await db.commit()
    await db.refresh(patch)
    return _patch_out(patch)


@router.post("/organizations/{org_id}/cleanup/patches/{patch_id}/refresh-pr")
async def refresh_pull_request(
    org_id: uuid.UUID,
    patch_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    patch = await _patch_for_org(db, org_id, patch_id)
    if not patch.github_repository_full_name or not patch.github_pr_number:
        raise HTTPException(status_code=404, detail="This patch does not have a GitHub pull request.")
    connection, client = await _selected_github(db, org_id)
    if connection.repository_full_name != patch.github_repository_full_name:
        raise HTTPException(status_code=409, detail="Connect the repository containing this PR to refresh its status.")
    try:
        pr = await client.get_pull_request(patch.github_repository_full_name, patch.github_pr_number)
    except GitHubApiError as exc:
        raise map_github_error(exc)
    patch.github_pr_state = "merged" if pr.get("merged") else pr.get("state")
    await db.commit()
    await db.refresh(patch)
    return _patch_out(patch)
