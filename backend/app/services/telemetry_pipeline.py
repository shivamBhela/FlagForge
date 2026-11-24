import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.telemetry import TelemetryAggregate

logger = logging.getLogger("telemetry-pipeline")


class TelemetryPipeline:
    """Ingests OpenTelemetry metrics/traces and aggregates feature-attributed health metrics."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def record_metrics_batch(self, items: List[Dict[str, Any]]) -> int:
        """Records a batch of aggregated OpenTelemetry metrics attributed to feature flags."""
        count = 0
        for item in items:
            agg = TelemetryAggregate(
                organization_id=self.organization_id,
                service_name=item["service_name"],
                environment_name=item.get("environment_name", "production"),
                feature_flag_key=item.get("feature_flag_key"),
                window_start=item.get("window_start", datetime.now(timezone.utc) - timedelta(minutes=5)),
                window_end=item.get("window_end", datetime.now(timezone.utc)),
                request_count=item.get("request_count", 0),
                error_count=item.get("error_count", 0),
                error_rate=item.get("error_rate", 0.0),
                p50_ms=item.get("p50_ms", 50.0),
                p95_ms=item.get("p95_ms", 120.0),
                p99_ms=item.get("p99_ms", 250.0),
            )
            self.db.add(agg)
            count += 1
        await self.db.commit()
        return count

    async def get_metrics_for_flag(self, flag_key: str, environment_name: str = "production") -> Dict[str, Any]:
        """Retrieves aggregated metrics and baseline comparison for a specific feature flag."""
        stmt = (
            select(TelemetryAggregate)
            .where(
                TelemetryAggregate.organization_id == self.organization_id,
                TelemetryAggregate.feature_flag_key == flag_key,
                TelemetryAggregate.environment_name == environment_name,
            )
            .order_by(TelemetryAggregate.window_end.desc())
            .limit(10)
        )
        records = (await self.db.execute(stmt)).scalars().all()

        if not records:
            return {
                "flag_key": flag_key,
                "has_telemetry": False,
                "total_requests": 0,
                "avg_error_rate": 0.0,
                "avg_p95_ms": 0.0,
                "samples_count": 0,
            }

        total_reqs = sum(r.request_count for r in records)
        avg_err = sum(r.error_rate for r in records) / len(records)
        avg_p95 = sum(r.p95_ms for r in records) / len(records)

        return {
            "flag_key": flag_key,
            "has_telemetry": True,
            "total_requests": total_reqs,
            "avg_error_rate": round(avg_err, 4),
            "avg_p95_ms": round(avg_p95, 2),
            "samples_count": len(records),
            "series": [
                {
                    "time": r.window_end.isoformat(),
                    "requests": r.request_count,
                    "errors": r.error_count,
                    "error_rate": r.error_rate,
                    "p95_ms": r.p95_ms,
                }
                for r in reversed(records)
            ],
        }
