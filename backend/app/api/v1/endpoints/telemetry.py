import uuid
import hmac
import json
from datetime import datetime, timezone
from typing import Annotated, List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.organization import Organization
from app.models.project import Project
from app.core.config import settings
from app.services.telemetry_pipeline import TelemetryPipeline
from app.api.deps import require_org_member

router = APIRouter()


def _attribute_map(attributes: list[dict[str, Any]]) -> dict[str, Any]:
    values = {}
    for item in attributes:
        value = item.get("value") or {}
        values[item.get("key")] = next(iter(value.values()), None)
    return values


def _nano_time(value: Any) -> datetime:
    return datetime.fromtimestamp(int(value) / 1_000_000_000, tz=timezone.utc)


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
    try:
        count = await pipeline.record_metrics_batch(batch.items)
    except (TypeError, ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
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


@router.post("/telemetry/otlp/v1/metrics", status_code=202, include_in_schema=True)
async def ingest_otlp_metrics(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Optional[str] = Header(None),
):
    """Accept OTLP/HTTP JSON from the trusted local Collector and persist tenant-scoped histograms."""
    expected = f"Bearer {settings.OTEL_INGEST_TOKEN}" if settings.OTEL_INGEST_TOKEN else ""
    if not expected or not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Invalid telemetry exporter credential")
    raw = await request.body()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Telemetry batch is too large")
    try:
        envelope = json.loads(raw)
        resource_metrics = envelope["resourceMetrics"]
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=400, detail="Malformed OTLP metrics payload")

    parsed: dict[uuid.UUID, list[dict[str, Any]]] = {}
    project_ids: dict[uuid.UUID, uuid.UUID] = {}
    try:
        for resource_entry in resource_metrics:
            resource = _attribute_map((resource_entry.get("resource") or {}).get("attributes", []))
            org_id = uuid.UUID(str(resource.get("flagforge.organization_id")))
            project_id = uuid.UUID(str(resource.get("flagforge.project_id")))
            service_name = resource.get("service.name")
            environment_name = resource.get("deployment.environment")
            if not service_name or not environment_name:
                raise ValueError("Missing service or environment resource attributes")
            project_ids[org_id] = project_id
            for scope in resource_entry.get("scopeMetrics", []):
                for metric in scope.get("metrics", []):
                    histogram = metric.get("histogram")
                    if not histogram or metric.get("name") != "http.server.request.duration":
                        continue
                    scale = 1000.0 if metric.get("unit") == "s" else 1.0
                    if metric.get("unit") not in {"ms", "s"}:
                        raise ValueError("Request duration histogram unit must be ms or s")
                    for point in histogram.get("dataPoints", []):
                        attrs = _attribute_map(point.get("attributes", []))
                        count = int(point.get("count", 0))
                        if count <= 0:
                            continue
                        code = int(attrs.get("http.response.status_code", 200))
                        bounds = [float(value) * scale for value in point.get("explicitBounds", [])]
                        counts = [int(value) for value in point.get("bucketCounts", [])]
                        item = {
                            "project_id": str(project_id), "service_name": str(service_name),
                            "environment_name": str(environment_name),
                            "feature_flag_key": attrs.get("flagforge.feature_flag_key"),
                            "window_start": _nano_time(point["startTimeUnixNano"]),
                            "window_end": _nano_time(point["timeUnixNano"]),
                            "request_count": count, "error_count": count if code >= 500 else 0,
                            "latency_bucket_bounds": bounds, "latency_bucket_counts": counts,
                        }
                        parsed.setdefault(org_id, []).append(item)
    except (ValueError, KeyError, TypeError, OverflowError):
        raise HTTPException(status_code=422, detail="Invalid or incomplete OTLP resource or histogram attributes")

    total = 0
    for org_id, project_id in project_ids.items():
        organization = (await db.execute(select(Organization).where(Organization.id == org_id))).scalar_one_or_none()
        project = (await db.execute(select(Project).where(
            Project.id == project_id, Project.organization_id == org_id,
        ))).scalar_one_or_none()
        if organization is None or project is None:
            raise HTTPException(status_code=422, detail="Telemetry organization/project attribution is unknown")
        items = parsed.get(org_id, [])
        if items:
            total += await TelemetryPipeline(db=db, organization_id=org_id).record_metrics_batch(items)
    return {"accepted": True, "persisted_histogram_points": total}
