"""Redis-backed per-IP and per-account login throttling."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import AsyncGenerator

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_ACCOUNT_LIMIT = 8
LOGIN_IP_LIMIT = 100

_INCREMENT_WINDOW_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return {count, redis.call('TTL', KEYS[1])}
"""


async def get_login_rate_limit_redis() -> AsyncGenerator[Redis, None]:
    """Yield an isolated client; Redis connection pools close after each request."""
    client = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        yield client
    finally:
        await client.aclose()


def _rate_key(scope: str, identity: str) -> str:
    digest = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        f"{scope}\0{identity}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"flagforge:auth-login:v1:{scope}:{digest}"


async def enforce_login_rate_limit(request: Request, email: str, redis: Redis) -> None:
    """Count login attempts atomically without storing raw email or IP values."""
    client_ip = request.client.host if request.client else "unknown"
    normalized_email = email.strip().casefold()
    keys_and_limits = (
        (_rate_key("ip", client_ip), LOGIN_IP_LIMIT),
        (_rate_key("account", f"{client_ip}\0{normalized_email}"), LOGIN_ACCOUNT_LIMIT),
    )

    try:
        results = [
            await redis.eval(_INCREMENT_WINDOW_SCRIPT, 1, key, LOGIN_WINDOW_SECONDS)
            for key, _limit in keys_and_limits
        ]
    except RedisError:
        # Fail closed: allowing logins during a limiter outage would silently
        # remove the brute-force control.
        logger.error("Login rate-limit store is unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login protection is temporarily unavailable. Please retry shortly.",
        ) from None

    for (key, limit), result in zip(keys_and_limits, results):
        count, ttl = int(result[0]), int(result[1])
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later.",
                headers={"Retry-After": str(max(ttl, 1))},
            )


async def clear_account_login_attempts(request: Request, email: str, redis: Redis) -> None:
    """Clear account-specific failures after a successful authentication."""
    client_ip = request.client.host if request.client else "unknown"
    key = _rate_key("account", f"{client_ip}\0{email.strip().casefold()}")
    try:
        await redis.delete(key)
    except RedisError:
        # The successful login is valid; an uncleared counter expires naturally.
        logger.warning("Could not clear account login-attempt counter")
