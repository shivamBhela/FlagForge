import json
import uuid
from typing import Any
from redis.asyncio import Redis

STREAM = "flagforge:jobs"
GROUP = "flagforge-workers"
MAX_ATTEMPTS = 4


async def enqueue_job(redis: Redis, job_id: uuid.UUID, organization_id: uuid.UUID, job_type: str, payload: dict[str, Any]) -> None:
    await redis.xadd(STREAM, {
        "job_id": str(job_id),
        "organization_id": str(organization_id),
        "job_type": job_type,
        "payload": json.dumps(payload, separators=(",", ":")),
        "attempt": "0",
    })
