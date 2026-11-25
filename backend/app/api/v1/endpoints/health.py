from datetime import datetime, timezone
import time
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from app.core.config import settings
from app.core.database import async_engine

router = APIRouter()


def create_redis_client():
    # Import lazily so liveness remains available when optional local dependencies
    # have not been installed; readiness will report Redis as unavailable.
    from redis.asyncio import Redis

    return Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)


@router.get("/health", summary="Health Check")
@router.get("/healthz", summary="Liveness & Readiness Probe")
async def health_check(response: Response):
    """Deep health check verifying service status and downstream dependencies."""
    dependencies = {
        "postgres": {"status": "unavailable"},
        "redis": {"status": "unavailable"},
        "otel_collector": {
            "status": "configured_not_probed",
            "endpoint": settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        },
    }

    # Probe the configured database rather than treating configuration as health.
    try:
        t0 = time.perf_counter()
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        latency = (time.perf_counter() - t0) * 1000
        dependencies["postgres"]["status"] = "healthy"
        dependencies["postgres"]["latency_ms"] = round(latency, 2)
    except Exception:
        dependencies["postgres"]["status"] = "unavailable"

    # Probe Redis and always close the short-lived client.
    redis_client = None
    try:
        t0 = time.perf_counter()
        redis_client = create_redis_client()
        await redis_client.ping()
        latency = (time.perf_counter() - t0) * 1000
        dependencies["redis"]["status"] = "healthy"
        dependencies["redis"]["latency_ms"] = round(latency, 2)
    except Exception:
        dependencies["redis"]["status"] = "unavailable"
    finally:
        if redis_client is not None:
            try:
                await redis_client.aclose()
            except Exception:
                pass

    is_healthy = all(dependencies[name]["status"] == "healthy" for name in ("postgres", "redis"))
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": "flagforge-api",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": dependencies,
    }
