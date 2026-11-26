from bisect import bisect_left
from datetime import datetime, timezone
import logging
import os
import time

import httpx
from fastapi import FastAPI, HTTPException, Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("flagforge-demo")
app = FastAPI(title="FlagForge Demo Instrumented App", version="1.0.0")


async def emit_request_histogram(route: str, status_code: int, duration_ms: float, start_ns: int, end_ns: int) -> None:
    """Emit one OTLP/HTTP JSON histogram point to the Collector for a measured request."""
    organization_id = os.getenv("FLAGFORGE_ORGANIZATION_ID", "").strip()
    project_id = os.getenv("FLAGFORGE_PROJECT_ID", "").strip()
    if not organization_id or not project_id:
        return
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318").rstrip("/")
    if endpoint.endswith("/v1"):
        endpoint = endpoint[:-3]
    bounds = [1, 5, 10, 25, 50, 100, 200, 500, 1000, 2500]
    bucket_counts = [0] * (len(bounds) + 1)
    bucket_counts[bisect_left(bounds, max(0.0, duration_ms))] = 1
    payload = {
        "resourceMetrics": [{
            "resource": {"attributes": [
                {"key": "service.name", "value": {"stringValue": "flagforge-demo-app"}},
                {"key": "flagforge.organization_id", "value": {"stringValue": organization_id}},
                {"key": "flagforge.project_id", "value": {"stringValue": project_id}},
                {"key": "deployment.environment", "value": {"stringValue": os.getenv("FLAGFORGE_ENVIRONMENT_NAME", "staging")}},
            ]},
            "scopeMetrics": [{"scope": {"name": "flagforge-demo-app"}, "metrics": [{
                "name": "http.server.request.duration", "unit": "ms",
                "histogram": {"aggregationTemporality": 2, "dataPoints": [{
                    "attributes": [
                        {"key": "http.route", "value": {"stringValue": route}},
                        {"key": "http.response.status_code", "value": {"intValue": str(status_code)}},
                        {"key": "flagforge.feature_flag_key", "value": {"stringValue": "checkout_v2_redesign"}},
                    ],
                    "startTimeUnixNano": str(start_ns),
                    "timeUnixNano": str(end_ns),
                    "count": "1",
                    "sum": duration_ms,
                    "explicitBounds": bounds,
                    "bucketCounts": [str(value) for value in bucket_counts],
                }]},
            }]}],
        }],
    }
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            response = await client.post(f"{endpoint}/v1/metrics", json=payload)
            response.raise_for_status()
    except (httpx.HTTPError, ValueError):
        logger.warning("OTLP request histogram export failed", extra={"route": route})


@app.middleware("http")
async def record_http_metrics(request: Request, call_next):
    if request.url.path in {"/health", "/healthz"}:
        return await call_next(request)
    started = time.perf_counter()
    started_at_ns = time.time_ns()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        await emit_request_histogram(request.url.path, status_code, (time.perf_counter() - started) * 1000,
                                     started_at_ns, time.time_ns())


@app.get("/healthz")
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "flagforge-demo-app",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/checkout")
def checkout(user_id: str = "user-123", fail: bool = False):
    if fail:
        raise HTTPException(status_code=500, detail="QA-requested demo failure")
    is_canary = hash(user_id) % 4 == 0
    return {
        "checkout_version": "v2_canary" if is_canary else "v1_legacy",
        "status": "success",
        "feature_flag": "checkout_v2_redesign",
        "user_id": user_id,
    }
