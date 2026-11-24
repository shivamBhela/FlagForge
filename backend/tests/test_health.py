from fastapi.testclient import TestClient
from app.main import app

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


def test_api_v1_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "flagforge-api"
    assert "dependencies" in data
    assert "postgres" in data["dependencies"]
    assert "redis" in data["dependencies"]


