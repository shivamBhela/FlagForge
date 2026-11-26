import json
import uuid
from typing import Annotated, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_org_admin, require_org_member
from app.core.config import settings
from app.core.database import get_db
from app.models.background_job import BackgroundJob
from app.models.code_intelligence import Repository
from app.models.flagsmith import FlagsmithConnection
from app.models.organization import OrganizationMember
from app.services.job_queue import enqueue_job

router = APIRouter()


class ScanJobInput(BaseModel):
    repository_id: uuid.UUID
    commit_sha: str = "HEAD"
    branch: Optional[str] = None
    custom_files: Optional[dict[str, str]] = None


class SyncJobInput(BaseModel):
    connection_id: uuid.UUID


async def _submit(db: AsyncSession, org_id: uuid.UUID, kind: str, payload: dict[str, Any]) -> BackgroundJob:
    job = BackgroundJob(organization_id=org_id, job_type=kind, payload=json.dumps(payload))
    db.add(job)
    await db.commit()
    await db.refresh(job)
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=3)
    try:
        await enqueue_job(redis, job.id, org_id, kind, payload)
    except Exception as exc:
        job.status = "FAILED"
        job.error = "Queue is unavailable; the job was not submitted."
        await db.commit()
        raise HTTPException(status_code=503, detail="Background queue is unavailable") from exc
    finally:
        await redis.aclose()
    return job


def _job_json(job: BackgroundJob) -> dict[str, Any]:
    return {"id": str(job.id), "organization_id": str(job.organization_id), "job_type": job.job_type,
            "status": job.status, "payload": json.loads(job.payload), "attempts": job.attempts,
            "result": json.loads(job.result) if job.result else None, "error": job.error,
            "created_at": job.created_at.isoformat(), "updated_at": job.updated_at.isoformat()}


@router.post("/organizations/{org_id}/jobs/flagsmith-sync", status_code=status.HTTP_202_ACCEPTED)
async def submit_flagsmith_sync(
    org_id: uuid.UUID, body: SyncJobInput,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    connection = (await db.execute(select(FlagsmithConnection).where(
        FlagsmithConnection.id == body.connection_id,
        FlagsmithConnection.organization_id == org_id,
    ))).scalar_one_or_none()
    if connection is None:
        raise HTTPException(status_code=404, detail="Flagsmith connection not found")
    return _job_json(await _submit(db, org_id, "flagsmith.sync", {"connection_id": str(body.connection_id)}))


@router.post("/organizations/{org_id}/jobs/repository-scan", status_code=status.HTTP_202_ACCEPTED)
async def submit_repository_scan(
    org_id: uuid.UUID, body: ScanJobInput,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repository = (await db.execute(select(Repository).where(
        Repository.id == body.repository_id, Repository.organization_id == org_id,
    ))).scalar_one_or_none()
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    payload = body.model_dump(exclude_none=True)
    payload["repository_id"] = str(body.repository_id)
    return _job_json(await _submit(db, org_id, "repository.scan", payload))


@router.get("/organizations/{org_id}/jobs")
async def list_jobs(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
):
    limit = min(max(limit, 1), 100)
    jobs = (await db.execute(select(BackgroundJob).where(
        BackgroundJob.organization_id == org_id,
    ).order_by(BackgroundJob.created_at.desc()).limit(limit))).scalars().all()
    return [_job_json(job) for job in jobs]


@router.get("/organizations/{org_id}/jobs/{job_id}")
async def get_job(
    org_id: uuid.UUID, job_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    job = (await db.execute(select(BackgroundJob).where(
        BackgroundJob.id == job_id, BackgroundJob.organization_id == org_id,
    ))).scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_json(job)
