import os
import asyncio
import time
import pytest
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import get_db
from app.core.login_rate_limit import get_login_rate_limit_redis
from app.models.base import Base

TEST_DB_FILE = "./flagforge_test.db"
test_engine = create_async_engine(
    f"sqlite+aiosqlite:///{TEST_DB_FILE}",
    echo=False,
)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class InMemoryLoginRateLimitRedis:
    """Deterministic Redis substitute for auth API tests; no network service needed."""

    def __init__(self):
        self._values: dict[str, tuple[int, float]] = {}

    async def eval(self, _script: str, _numkeys: int, key: str, window: int):
        now = time.monotonic()
        count, expires_at = self._values.get(key, (0, now))
        if expires_at <= now:
            count = 0
        count += 1
        expires_at = expires_at if count > 1 else now + int(window)
        self._values[key] = (count, expires_at)
        return [count, max(int(expires_at - now), 0)]

    async def delete(self, key: str):
        return int(self._values.pop(key, None) is not None)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes the database schema once for the test session."""
    async def init():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(init())

    yield

    async def cleanup():
        await test_engine.dispose()
    asyncio.run(cleanup())
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest.fixture
def client():
    """Provides a TestClient with overridden get_db dependency."""
    app.dependency_overrides[get_db] = override_get_db
    test_redis = InMemoryLoginRateLimitRedis()

    async def override_login_rate_limit_redis():
        yield test_redis

    app.dependency_overrides[get_login_rate_limit_redis] = override_login_rate_limit_redis
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_login_rate_limit_redis, None)
