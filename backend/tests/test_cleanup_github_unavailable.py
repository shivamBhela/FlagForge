import asyncio

from app.models.cleanup import CleanupPatch
from conftest import TestingSessionLocal


def test_cleanup_does_not_claim_a_github_pr_without_integration(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "cleanup.review@flagforge.io", "password": "Password123!", "full_name": "Cleanup Reviewer"},
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "cleanup.review@flagforge.io", "password": "Password123!"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_id = client.post(
        "/api/v1/organizations", json={"name": "Cleanup Review Org"}, headers=headers
    ).json()["id"]

    async def add_review_patch():
        async with TestingSessionLocal() as session:
            patch = CleanupPatch(
                organization_id=org_id,
                flag_key="stale_checkout_flag",
                file_path="src/checkout.ts",
                rationale="No source references remain.",
                diff_preview="--- a/src/checkout.ts\n+++ b/src/checkout.ts\n",
            )
            session.add(patch)
            await session.commit()
            return str(patch.id)

    patch_id = asyncio.run(add_review_patch())
    response = client.post(
        f"/api/v1/organizations/{org_id}/cleanup/patches/{patch_id}/create-pr",
        headers=headers,
    )

    assert response.status_code == 501
    assert "GitHub App integration is not configured" in response.json()["detail"]
