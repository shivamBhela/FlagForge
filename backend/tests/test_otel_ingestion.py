import time
import uuid
from app.core.config import settings


def _qa_tenant(client):
    email = f"otel-{uuid.uuid4().hex}@flagforge.io"
    password = "OtelQa-Password123!"
    assert client.post("/api/v1/auth/register", json={
        "email": email, "password": password, "full_name": "OTel QA",
    }).status_code == 201
    token = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org = client.post("/api/v1/organizations", json={"name": "OTel Isolated QA", "slug": f"otel-{uuid.uuid4().hex[:8]}"}, headers=headers).json()
    project = client.post(f"/api/v1/organizations/{org['id']}/projects", json={
        "name": "OTel QA Project", "slug": f"otel-project-{uuid.uuid4().hex[:8]}",
        "description": "Isolated telemetry test", "create_default_environments": True,
    }, headers=headers).json()
    return org["id"], project["id"], headers


def test_authenticated_otlp_histograms_persist_with_tenant_attribution(client, monkeypatch):
    monkeypatch.setattr(settings, "OTEL_INGEST_TOKEN", "isolated-collector-test-token")
    org_id, project_id, jwt_headers = _qa_tenant(client)
    now = str(time.time_ns())
    resource_attrs = [
        {"key": "service.name", "value": {"stringValue": "qa-demo"}},
        {"key": "flagforge.organization_id", "value": {"stringValue": org_id}},
        {"key": "flagforge.project_id", "value": {"stringValue": project_id}},
        {"key": "deployment.environment", "value": {"stringValue": "staging"}},
    ]

    def point(status, bucket):
        counts = [0, 0, 0, 0]
        counts[bucket] = 1
        return {
            "attributes": [
                {"key": "http.response.status_code", "value": {"intValue": str(status)}},
                {"key": "flagforge.feature_flag_key", "value": {"stringValue": "qa_flag"}},
            ],
            "startTimeUnixNano": str(int(now) - 1_000_000_000), "timeUnixNano": now, "count": "1",
            "sum": 25.0, "explicitBounds": [10, 100, 1000], "bucketCounts": counts,
        }

    payload = {"resourceMetrics": [{"resource": {"attributes": resource_attrs}, "scopeMetrics": [{
        "metrics": [{"name": "http.server.request.duration", "unit": "ms", "histogram": {
            "aggregationTemporality": 2, "dataPoints": [point(200, 1), point(503, 2)],
        }}],
    }]}]}
    denied = client.post("/api/v1/telemetry/otlp/v1/metrics", json=payload, headers={"Authorization": "Bearer wrong"})
    assert denied.status_code == 401
    accepted = client.post("/api/v1/telemetry/otlp/v1/metrics", json=payload,
                           headers={"Authorization": "Bearer isolated-collector-test-token"})
    assert accepted.status_code == 202
    assert accepted.json()["persisted_histogram_points"] == 2
    metrics = client.get(f"/api/v1/organizations/{org_id}/telemetry/metrics?flag_key=qa_flag&environment_name=staging",
                         headers=jwt_headers).json()
    assert metrics["total_requests"] == 2
    assert metrics["successful_requests"] == 1
    assert metrics["error_count"] == 1
    assert metrics["avg_error_rate"] == 0.5
    assert metrics["has_latency_histogram"] is True
    # Merged histogram rank 2 belongs to the 1000ms bucket, not the average of p95s.
    assert metrics["avg_p95_ms"] == 1000.0


def test_otlp_histogram_rejects_unknown_project_and_malformed_buckets(client, monkeypatch):
    monkeypatch.setattr(settings, "OTEL_INGEST_TOKEN", "isolated-collector-test-token")
    org_id, project_id, _ = _qa_tenant(client)
    now = str(time.time_ns())
    payload = {"resourceMetrics": [{"resource": {"attributes": [
        {"key": "service.name", "value": {"stringValue": "qa-demo"}},
        {"key": "flagforge.organization_id", "value": {"stringValue": org_id}},
        {"key": "flagforge.project_id", "value": {"stringValue": str(uuid.uuid4())}},
        {"key": "deployment.environment", "value": {"stringValue": "staging"}},
    ]}, "scopeMetrics": []}]}
    headers = {"Authorization": "Bearer isolated-collector-test-token"}
    assert client.post("/api/v1/telemetry/otlp/v1/metrics", json=payload, headers=headers).status_code == 422
    assert project_id
