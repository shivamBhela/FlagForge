from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.endpoints import health

client = TestClient(app)


def test_root_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "flagforge-api"
    assert "timestamp" in data


def test_root_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def patch_health_dependencies(monkeypatch, *, redis_available=True):
    class Connection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def execute(self, _statement):
            return 1

    class Engine:
        def connect(self):
            return Connection()

    class RedisClient:
        async def ping(self):
            if not redis_available:
                raise ConnectionError("unavailable")
            return True

        async def aclose(self):
            return None

    monkeypatch.setattr(health, "async_engine", Engine())
    monkeypatch.setattr(health, "create_redis_client", lambda: RedisClient())


def test_api_v1_health_reports_live_dependency_probes(monkeypatch):
    patch_health_dependencies(monkeypatch)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "flagforge-api"
    assert "dependencies" in data
    assert "postgres" in data["dependencies"]
    assert "redis" in data["dependencies"]
    assert data["dependencies"]["postgres"]["status"] == "healthy"
    assert data["dependencies"]["redis"]["status"] == "healthy"


def test_api_v1_health_is_degraded_when_redis_is_unavailable(monkeypatch):
    patch_health_dependencies(monkeypatch, redis_available=False)
    response = client.get("/api/v1/healthz")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["postgres"]["status"] == "healthy"
    assert data["dependencies"]["redis"]["status"] == "unavailable"


