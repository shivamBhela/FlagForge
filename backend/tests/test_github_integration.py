import asyncio
import uuid

from app.core.crypto import encrypt_secret
from app.models.cleanup import CleanupPatch, PatchStatus
from app.models.github import GitHubConnection
from conftest import TestingSessionLocal


class FakeGitHubClient:
    def __init__(self):
        self.base = "a" * 40
        self.blob = "b" * 40
        self.commit = "c" * 40
        self.original = 'if flagsmith.hasFeature("checkout_v2"):\n    return modern()\nreturn legacy()\n'
        self.replacement = None
        self.refs = {"main": self.base}
        self.pull_requests = []
        self.default_branch_writes = 0

    async def get_ref(self, full_name, branch):
        return self.refs[branch]

    async def get_file(self, full_name, path, ref):
        return (self.replacement if ref != self.base and self.replacement is not None else self.original), self.blob

    async def create_branch(self, full_name, branch, base_sha):
        assert branch.startswith("flagforge/cleanup-")
        assert branch != "main"
        assert base_sha == self.base
        self.refs[branch] = base_sha

    async def put_file(self, full_name, path, branch, content, old_sha, message):
        assert branch != "main"
        self.replacement = content
        self.refs[branch] = self.commit
        return {"commit": {"sha": self.commit}}

    async def find_pull_request(self, full_name, branch, base):
        return next((pr for pr in self.pull_requests if pr["head"]["ref"] == branch and pr["base"]["ref"] == base), None)

    async def create_pull_request(self, full_name, branch, base, title, body):
        pr = {"number": 42, "state": "open", "html_url": "https://github.com/acme/shop/pull/42", "head": {"ref": branch}, "base": {"ref": base}}
        self.pull_requests.append(pr)
        return pr

    async def get_commit(self, full_name, sha):
        return {"parents": [{"sha": self.base}]}

    async def get_pull_request(self, full_name, number):
        return {"number": number, "state": "closed", "merged": False}


def _auth_and_org(client, email):
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "QA Admin"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org = client.post("/api/v1/organizations", json={"name": "GitHub QA Org"}, headers=headers).json()
    return headers, org["id"]


def test_fine_grained_github_client_limits_api_and_sanitizes_repository_response(monkeypatch):
    import httpx
    from app.services.github_client import GitHubClient

    requests = []
    async def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[{
            "id": 17,
            "full_name": "acme/shop",
            "private": True,
            "default_branch": "main",
            "permissions": {"pull": True, "push": True},
            "html_url": "https://github.com/acme/shop",
        }])

    async def run():
        client = GitHubClient("ghp_unit_test_token", transport=httpx.MockTransport(handler))
        return await client.list_repositories("FINE_GRAINED_PAT")

    repos = asyncio.run(run())
    assert repos == [{"id": 17, "full_name": "acme/shop", "private": True, "default_branch": "main", "permissions": {"pull": True, "push": True}, "html_url": "https://github.com/acme/shop"}]
    assert requests[0].url.host == "api.github.com"
    assert requests[0].headers["Authorization"] == "Bearer ghp_unit_test_token"
    assert "token" not in str(repos).lower()


def test_reviewed_patch_creates_idempotent_pr_on_separate_branch(client, monkeypatch):
    headers, org_id = _auth_and_org(client, "github.pr.admin@flagforge.io")
    fake = FakeGitHubClient()

    async def fake_client(_connection):
        return fake

    monkeypatch.setattr("app.api.v1.endpoints.cleanup.get_client_for_connection", fake_client)

    async def seed():
        async with TestingSessionLocal() as session:
            session.add(GitHubConnection(
                organization_id=uuid.UUID(org_id),
                credential_type="FINE_GRAINED_PAT",
                encrypted_token=encrypt_secret("fine-grained-test-token"),
                repository_full_name="acme/shop",
                default_branch="main",
            ))
            patch = CleanupPatch(
                organization_id=uuid.UUID(org_id),
                flag_key="checkout_v2",
                file_path="src/checkout.ts",
                rationale="Reviewed test cleanup.",
                diff_preview="",
            )
            session.add(patch)
            await session.commit()
            return str(patch.id)

    patch_id = asyncio.run(seed())
    source = client.get(f"/api/v1/organizations/{org_id}/cleanup/patches/{patch_id}/github-source", headers=headers)
    assert source.status_code == 200
    source_data = source.json()
    assert source_data["content"] == fake.original
    replacement = 'return modern()\n'
    prepared = client.put(
        f"/api/v1/organizations/{org_id}/cleanup/patches/{patch_id}/github-preview",
        headers=headers,
        json={
            "base_file_sha": source_data["base_file_sha"],
            "base_commit_sha": source_data["base_commit_sha"],
            "replacement_content": replacement,
        },
    )
    assert prepared.status_code == 200
    assert "-return legacy()" in prepared.json()["diff_preview"]

    response = client.post(
        f"/api/v1/organizations/{org_id}/cleanup/patches/{patch_id}/create-pr",
        headers=headers,
        json={"approved": True},
    )
    assert response.status_code == 200, response.text
    assert response.json()["github_pr_number"] == 42
    assert response.json()["pr_url"] == "https://github.com/acme/shop/pull/42"
    assert response.json()["github_branch"].startswith("flagforge/cleanup-")
    assert fake.refs["main"] == fake.base
    assert fake.replacement == replacement

    again = client.post(
        f"/api/v1/organizations/{org_id}/cleanup/patches/{patch_id}/create-pr",
        headers=headers,
        json={"approved": True},
    )
    assert again.status_code == 200
    assert len(fake.pull_requests) == 1


def test_github_connection_and_patch_routes_are_tenant_scoped(client):
    owner_headers, owner_org = _auth_and_org(client, "github.tenant.owner@flagforge.io")
    other_headers, other_org = _auth_and_org(client, "github.tenant.other@flagforge.io")

    response = client.get(f"/api/v1/organizations/{owner_org}/github/connection", headers=other_headers)
    assert response.status_code == 403
    response = client.put(
        f"/api/v1/organizations/{other_org}/cleanup/patches/{uuid.uuid4()}/github-preview",
        headers=owner_headers,
        json={"base_file_sha": "a" * 40, "base_commit_sha": "b" * 40, "replacement_content": "safe"},
    )
    assert response.status_code == 403


def test_patch_preview_rejects_repository_from_another_organization(client):
    headers, org_id = _auth_and_org(client, "github.repository.scope@flagforge.io")
    response = client.post(
        f"/api/v1/organizations/{org_id}/cleanup/patches/preview",
        headers=headers,
        json={"flag_key": "old_flag", "file_path": "src/a.ts", "repository_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404
