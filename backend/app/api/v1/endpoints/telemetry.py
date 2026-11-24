import uuid
from typing import Annotated, List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.services.telemetry_pipeline import TelemetryPipeline
from app.api.deps import require_org_member

router = APIRouter()


class MetricBatchInput(BaseModel):
    items: List[Dict[str, Any]]


@router.post("/organizations/{org_id}/telemetry/ingest")
async def ingest_telemetry(
    org_id: uuid.UUID,
    batch: MetricBatchInput,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    pipeline = TelemetryPipeline(db=db, organization_id=org_id)
    count = await pipeline.record_metrics_batch(batch.items)
    return {"ok": True, "ingested_records": count}


@router.get("/organizations/{org_id}/telemetry/metrics")
async def get_metrics(
    org_id: uuid.UUID,
    flag_key: str,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    environment_name: str = "production",
):
    pipeline = TelemetryPipeline(db=db, organization_id=org_id)
    return await pipeline.get_metrics_for_flag(flag_key=flag_key, environment_name=environment_name)
