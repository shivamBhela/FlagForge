import uuid
from app.api.v1.endpoints import jobs as jobs_endpoint


def _org(client, email):
    register = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Password123!", "full_name": "Queue QA",
    })
    assert register.status_code == 201
    token = client.post("/api/v1/auth/login", json={
        "email": email, "password": "Password123!",
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org = client.post("/api/v1/organizations", json={"name": "Queue QA", "slug": f"queue-{uuid.uuid4().hex[:8]}"}, headers=headers)
    assert org.status_code == 201
    return org.json()["id"], headers


def test_job_submission_persists_and_scopes_to_organization(client, monkeypatch):
    queued = []

    async def fake_enqueue(redis, job_id, organization_id, job_type, payload):
        queued.append((str(job_id), str(organization_id), job_type, payload))

    monkeypatch.setattr(jobs_endpoint, "enqueue_job", fake_enqueue)
    org_id, headers = _org(client, f"queue-{uuid.uuid4().hex}@flagforge.io")
    repository = client.post(
        f"/api/v1/organizations/{org_id}/repositories",
        json={"name": "qa-repository", "repo_url": "https://example.invalid/qa", "language": "typescript"},
        headers=headers,
    )
    assert repository.status_code == 201
    submitted = client.post(
        f"/api/v1/organizations/{org_id}/jobs/repository-scan",
        json={"repository_id": repository.json()["id"], "custom_files": {"src/qa.ts": "flagsmith.hasFeature('qa_flag')"}},
        headers=headers,
    )
    assert submitted.status_code == 202
    body = submitted.json()
    assert body["status"] == "PENDING"
    assert body["job_type"] == "repository.scan"
    assert len(queued) == 1 and queued[0][0] == body["id"]

    status_response = client.get(f"/api/v1/organizations/{org_id}/jobs/{body['id']}", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["payload"]["repository_id"] == repository.json()["id"]

    other_org, other_headers = _org(client, f"queue-other-{uuid.uuid4().hex}@flagforge.io")
    assert client.get(f"/api/v1/organizations/{other_org}/jobs/{body['id']}", headers=other_headers).status_code == 404
    assert client.get(f"/api/v1/organizations/{other_org}/jobs", headers=other_headers).json() == []


def test_job_submission_rejects_cross_tenant_repository(client, monkeypatch):
    async def fake_enqueue(*args, **kwargs):
        raise AssertionError("cross-tenant references must fail before enqueue")

    monkeypatch.setattr(jobs_endpoint, "enqueue_job", fake_enqueue)
    first_org, first_headers = _org(client, f"queue-a-{uuid.uuid4().hex}@flagforge.io")
    second_org, second_headers = _org(client, f"queue-b-{uuid.uuid4().hex}@flagforge.io")
    repository = client.post(
        f"/api/v1/organizations/{first_org}/repositories",
        json={"name": "private", "repo_url": "https://example.invalid/private"},
        headers=first_headers,
    ).json()
    result = client.post(
        f"/api/v1/organizations/{second_org}/jobs/repository-scan",
        json={"repository_id": repository["id"]},
        headers=second_headers,
    )
    assert result.status_code == 404
