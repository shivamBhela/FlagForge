"""Redis Streams worker with durable status, retries, and restart recovery."""
import asyncio
import json
import logging
import os
import signal
import socket
import uuid
from datetime import datetime, timezone

from redis.asyncio import Redis
from redis.exceptions import ResponseError
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.background_job import BackgroundJob
from app.models.code_intelligence import Repository
from app.models.flagsmith import FlagsmithConnection, SyncTrigger
from app.services.flagsmith_sync import FlagsmithSyncEngine
from app.services.scanner import CodeScanner
from app.services.job_queue import GROUP, MAX_ATTEMPTS, STREAM

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("flagforge-worker")
HEALTH_KEY = "flagforge:worker:heartbeat"
HEARTBEAT_SECONDS = 10
CLAIM_IDLE_MS = 60_000


async def run_job(redis: Redis, fields: dict[str, str]) -> None:
    job_id = uuid.UUID(fields["job_id"])
    organization_id = uuid.UUID(fields["organization_id"])
    job_type = fields["job_type"]
    payload = json.loads(fields["payload"])
    attempt = int(fields.get("attempt", "0")) + 1

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BackgroundJob).where(
                BackgroundJob.id == job_id,
                BackgroundJob.organization_id == organization_id,
            )
        )
        job = result.scalar_one_or_none()
        if job is None:
            logger.error("Discarding job with no matching tenant status record", extra={"job_id": str(job_id)})
            return
        if job.status == "COMPLETED":
            return
        job.status = "RUNNING"
        job.attempts = attempt
        job.error = None
        await db.commit()

        try:
            if job_type == "flagsmith.sync":
                connection_id = uuid.UUID(payload["connection_id"])
                connection = (await db.execute(select(FlagsmithConnection).where(
                    FlagsmithConnection.id == connection_id,
                    FlagsmithConnection.organization_id == organization_id,
                ))).scalar_one_or_none()
                if connection is None:
                    raise ValueError("Flagsmith connection does not belong to the job organization")
                sync = await FlagsmithSyncEngine(db=db, connection=connection).run_sync(trigger=SyncTrigger.MANUAL)
                output = {"sync_id": str(sync.id), "status": sync.status.value,
                          "created": sync.records_created, "updated": sync.records_updated,
                          "unchanged": sync.records_unchanged}
            elif job_type == "repository.scan":
                repository_id = uuid.UUID(payload["repository_id"])
                repository = (await db.execute(select(Repository).where(
                    Repository.id == repository_id,
                    Repository.organization_id == organization_id,
                ))).scalar_one_or_none()
                if repository is None:
                    raise ValueError("Repository does not belong to the job organization")
                scan = await CodeScanner(db=db, organization_id=organization_id).execute_scan(
                    repository_id=repository_id,
                    commit_sha=payload.get("commit_sha", "HEAD"),
                    branch=payload.get("branch", repository.default_branch),
                    custom_files=payload.get("custom_files"),
                    background_job_id=job_id,
                )
                output = {"scan_id": str(scan.id), "status": scan.status.value,
                          "references_found": scan.findings_count}
            else:
                raise ValueError("Unsupported job type")
            job.status = "COMPLETED"
            job.result = json.dumps(output, separators=(",", ":"))
            job.error = None
            await db.commit()
            logger.info("Background job completed", extra={"job_id": str(job_id), "job_type": job_type,
                                                               "organization_id": str(organization_id)})
        except Exception as exc:
            await db.rollback()
            job = (await db.execute(select(BackgroundJob).where(
                BackgroundJob.id == job_id, BackgroundJob.organization_id == organization_id,
            ))).scalar_one_or_none()
            if job is not None:
                job.attempts = attempt
                job.error = str(exc)[:1000]
                job.status = "PENDING" if attempt < MAX_ATTEMPTS else "FAILED"
                await db.commit()
            if attempt < MAX_ATTEMPTS:
                delay_ms = min(30_000, 500 * (2 ** (attempt - 1)))
                await asyncio.sleep(delay_ms / 1000)
                await redis.xadd(STREAM, {**fields, "attempt": str(attempt)})
                logger.warning("Background job scheduled for retry", extra={"job_id": str(job_id),
                                                                            "attempt": attempt})
            else:
                logger.exception("Background job failed permanently", extra={"job_id": str(job_id),
                                                                               "job_type": job_type})


async def main() -> None:
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5)
    await redis.ping()
    try:
        await redis.xgroup_create(STREAM, GROUP, id="0-0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
    consumer = f"{socket.gethostname()}-{os.getpid()}"
    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown.set)
        except NotImplementedError:
            pass
    logger.info("Worker ready", extra={"consumer": consumer})
    try:
        while not shutdown.is_set():
            await redis.set(HEALTH_KEY, datetime.now(timezone.utc).isoformat(), ex=30)
            try:
                reclaimed = await redis.xautoclaim(STREAM, GROUP, consumer, min_idle_time=CLAIM_IDLE_MS,
                                                   start_id="0-0", count=1)
                messages = reclaimed[1]
            except (ResponseError, AttributeError):
                messages = []
            if not messages:
                response = await redis.xreadgroup(GROUP, consumer, {STREAM: ">"}, count=1, block=1000)
                messages = response[0][1] if response else []
            for message_id, fields in messages:
                try:
                    await run_job(redis, fields)
                except Exception:
                    logger.exception("Worker could not process stream message")
                finally:
                    await redis.xack(STREAM, GROUP, message_id)
    finally:
        await redis.delete(HEALTH_KEY)
        await redis.aclose()
        logger.info("Worker stopped cleanly")


if __name__ == "__main__":
    asyncio.run(main())
