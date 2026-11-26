import uuid
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.telemetry import TelemetryAggregate

logger = logging.getLogger("telemetry-pipeline")


def _validate_histogram(bounds: Any, counts: Any) -> tuple[list[float], list[int]]:
    if not isinstance(bounds, list) or not isinstance(counts, list) or len(counts) != len(bounds) + 1:
        raise ValueError("Latency histogram requires N explicit bounds and N+1 bucket counts")
    parsed_bounds = [float(value) for value in bounds]
    parsed_counts = [int(value) for value in counts]
    if any(not math.isfinite(value) or value < 0 for value in parsed_bounds):
        raise ValueError("Latency histogram bounds must be finite and non-negative")
    if parsed_bounds != sorted(set(parsed_bounds)):
        raise ValueError("Latency histogram bounds must be strictly increasing")
    if any(value < 0 for value in parsed_counts):
        raise ValueError("Latency histogram bucket counts cannot be negative")
    return parsed_bounds, parsed_counts


def histogram_quantile(bounds: list[float], counts: list[int], quantile: float) -> Optional[float]:
    """Return the bucket upper bound containing the requested rank, never average quantiles."""
    if not counts or sum(counts) == 0:
        return None
    rank = max(1, math.ceil(sum(counts) * quantile))
    cumulative = 0
    for index, count in enumerate(counts):
        cumulative += count
        if cumulative >= rank:
            # The final bucket is +Inf; no defensible finite percentile is available.
            return bounds[index] if index < len(bounds) else None
    return None


def _merge_histograms(records: list[TelemetryAggregate]) -> tuple[list[float], list[int]]:
    bounds = sorted({float(bound) for record in records for bound in (record.latency_bucket_bounds or [])})
    merged = [0] * (len(bounds) + 1)
    for record in records:
        source_bounds = record.latency_bucket_bounds or []
        source_counts = record.latency_bucket_counts or []
        if len(source_counts) != len(source_bounds) + 1:
            continue
        for index, count in enumerate(source_counts):
            upper = source_bounds[index] if index < len(source_bounds) else None
            target_index = bounds.index(upper) if upper is not None else len(bounds)
            merged[target_index] += int(count)
    return bounds, merged


class TelemetryPipeline:
    """Validates persisted request aggregates and derives latency percentiles from OTLP buckets."""

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def record_metrics_batch(self, items: List[Dict[str, Any]]) -> int:
        count = 0
        for item in items:
            service = item.get("service_name")
            requests = item.get("request_count")
            errors = item.get("error_count", 0)
            if not isinstance(service, str) or not service.strip():
                raise ValueError("service_name is required")
            if isinstance(requests, bool) or not isinstance(requests, int) or requests < 0:
                raise ValueError("request_count must be a non-negative integer")
            if isinstance(errors, bool) or not isinstance(errors, int) or errors < 0 or errors > requests:
                raise ValueError("error_count must be an integer between zero and request_count")
            end = item.get("window_end") or datetime.now(timezone.utc)
            start = item.get("window_start") or end - timedelta(minutes=5)
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace("Z", "+00:00"))
            if start.tzinfo is None or end.tzinfo is None or end <= start:
                raise ValueError("window_start and window_end must be ordered timezone-aware timestamps")
            bounds = counts = None
            if item.get("latency_bucket_bounds") is not None or item.get("latency_bucket_counts") is not None:
                bounds, counts = _validate_histogram(item.get("latency_bucket_bounds"), item.get("latency_bucket_counts"))
                if sum(counts) != requests:
                    raise ValueError("Latency histogram count must equal request_count")
            rate = errors / requests if requests else 0.0
            p50 = histogram_quantile(bounds, counts, .50) if bounds is not None else item.get("p50_ms", 0.0)
            p95 = histogram_quantile(bounds, counts, .95) if bounds is not None else item.get("p95_ms", 0.0)
            p99 = histogram_quantile(bounds, counts, .99) if bounds is not None else item.get("p99_ms", 0.0)
            agg = TelemetryAggregate(
                organization_id=self.organization_id,
                project_id=uuid.UUID(item["project_id"]) if item.get("project_id") else None,
                service_name=service.strip(),
                environment_name=item.get("environment_name", "production"),
                feature_flag_key=item.get("feature_flag_key"),
                window_start=start,
                window_end=end,
                request_count=requests,
                error_count=errors,
                error_rate=rate,
                p50_ms=p50 or 0.0,
                p95_ms=p95 or 0.0,
                p99_ms=p99 or 0.0,
                latency_bucket_bounds=bounds,
                latency_bucket_counts=counts,
            )
            self.db.add(agg)
            count += 1
        await self.db.commit()
        return count

    async def get_metrics_for_flag(self, flag_key: str, environment_name: str = "production") -> Dict[str, Any]:
        stmt = (
            select(TelemetryAggregate)
            .where(
                TelemetryAggregate.organization_id == self.organization_id,
                TelemetryAggregate.feature_flag_key == flag_key,
                TelemetryAggregate.environment_name == environment_name,
            )
            .order_by(TelemetryAggregate.window_end.desc())
            .limit(100)
        )
        records = (await self.db.execute(stmt)).scalars().all()
        if not records:
            return {"flag_key": flag_key, "environment_name": environment_name, "has_telemetry": False,
                    "has_latency_histogram": False, "total_requests": 0, "successful_requests": 0,
                    "error_count": 0, "avg_error_rate": 0.0, "avg_p95_ms": None, "p50_ms": None,
                    "p99_ms": None, "throughput_per_second": None, "samples_count": 0, "series": []}

        total_reqs = sum(r.request_count for r in records)
        total_errors = sum(r.error_count for r in records)
        bounds, bucket_counts = _merge_histograms(records)
        has_histogram = sum(bucket_counts) > 0
        latest = records[0]
        duration = max((latest.window_end - min(r.window_start for r in records)).total_seconds(), 0.001)
        return {
            "flag_key": flag_key,
            "environment_name": environment_name,
            "has_telemetry": True,
            "has_latency_histogram": has_histogram,
            "total_requests": total_reqs,
            "successful_requests": total_reqs - total_errors,
            "error_count": total_errors,
            "avg_error_rate": round(total_errors / total_reqs, 4) if total_reqs else 0.0,
            "avg_p95_ms": histogram_quantile(bounds, bucket_counts, .95) if has_histogram else None,
            "p50_ms": histogram_quantile(bounds, bucket_counts, .50) if has_histogram else None,
            "p99_ms": histogram_quantile(bounds, bucket_counts, .99) if has_histogram else None,
            "throughput_per_second": round(total_reqs / duration, 3),
            "samples_count": len(records),
            "window_start": min(r.window_start for r in records).isoformat(),
            "window_end": latest.window_end.isoformat(),
            "series": [
                {"time": r.window_end.isoformat(), "requests": r.request_count,
                 "errors": r.error_count, "error_rate": r.error_rate,
                 "p95_ms": histogram_quantile(r.latency_bucket_bounds or [], r.latency_bucket_counts or [], .95)
                 if r.latency_bucket_counts else None}
                for r in reversed(records)
            ],
        }
