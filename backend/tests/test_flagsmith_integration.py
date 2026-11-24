import hmac
import hashlib
import json
import pytest
from unittest.mock import patch, AsyncMock
from app.services.flagsmith_client import FlagsmithClient


@pytest.fixture
def mock_flagsmith_data():
    return {
        "projects": [
            {"id": 101, "name": "E-Commerce Platform", "organisation": 1}
        ],
        "environments": [
            {"id": 201, "name": "Production", "api_key": "ser.prod-key-101", "project": 101},
            {"id": 202, "name": "Staging", "api_key": "ser.staging-key-101", "project": 101},
        ],
        "features": [
            {"id": 301, "name": "checkout_v2_redesign", "type": "FLAG", "default_enabled": False, "description": "New checkout flow"},
            {"id": 302, "name": "instant_refunds", "type": "FLAG", "default_enabled": True, "description": "Auto refund approval"},
        ],
        "states_prod": [
            {"id": 401, "feature": 301, "enabled": False, "feature_state_value": None},
            {"id": 402, "feature": 302, "enabled": True, "feature_state_value": "tier-1"},
        ],
        "states_staging": [
            {"id": 403, "feature": 301, "enabled": True, "feature_state_value": None},
            {"id": 404, "feature": 302, "enabled": True, "feature_state_value": "tier-1"},
        ],
    }


def test_flagsmith_connection_lifecycle_and_security(client):
    # 1. Register User and create Organization
    client.post("/api/v1/auth/register", json={"email": "admin@cloudcorp.io", "password": "Password123!", "full_name": "Cloud Admin"})
    token = client.post("/api/v1/auth/login", json={"email": "admin@cloudcorp.io", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_org = client.post("/api/v1/organizations", json={"name": "Cloud Corp"}, headers=headers)
    assert res_org.status_code == 201
    org_id = res_org.json()["id"]

    # 2. SSRF Protection: Attempting to point to metadata / loopback address must be blocked
    ssrf_payload = {
        "name": "Malicious Metadata",
        "api_url": "http://169.254.169.254/latest/meta-data/",
        "token": "secret-token",
        "connection_type": "SELF_HOSTED",
    }
    res_ssrf = client.post(f"/api/v1/flagsmith/organizations/{org_id}/flagsmith/connections", json=ssrf_payload, headers=headers)
    assert res_ssrf.status_code == 400
    assert "protection" in res_ssrf.json()["detail"].lower() or "metadata" in res_ssrf.json()["detail"].lower()

    # 3. Create Valid Connection (mocking initial test call)
    with patch.object(FlagsmithClient, "test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = {"ok": True, "projects_count": 1}

        conn_payload = {
            "name": "Flagsmith Production Cloud",
            "api_url": "https://edge.api.flagsmith.com/api/v1",
            "token": "secret-flagsmith-mgmt-key-9999",
            "connection_type": "CLOUD",
            "webhook_secret": "my-secret-webhook-signing-key",
        }
        res_conn = client.post(f"/api/v1/flagsmith/organizations/{org_id}/flagsmith/connections", json=conn_payload, headers=headers)
        assert res_conn.status_code == 201
        conn_data = res_conn.json()
        assert conn_data["name"] == "Flagsmith Production Cloud"
        assert conn_data["api_url"] == "https://edge.api.flagsmith.com/api/v1"
        assert conn_data["has_token"] is True
        assert conn_data["has_webhook_secret"] is True
        # Verify secret token is NOT leaked in the response
        assert "token" not in conn_data
        assert "encrypted_token" not in conn_data
        conn_id = conn_data["id"]

    # 4. List connections for organization
    res_list = client.get(f"/api/v1/flagsmith/organizations/{org_id}/flagsmith/connections", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1


def test_idempotent_synchronization_and_flags_query(client, mock_flagsmith_data):
    # Setup user and org
    client.post("/api/v1/auth/register", json={"email": "sync.tester@flagforge.io", "password": "Password123!", "full_name": "Sync Tester"})
    token = client.post("/api/v1/auth/login", json={"email": "sync.tester@flagforge.io", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post("/api/v1/organizations", json={"name": "Sync Org"}, headers=headers).json()["id"]

    # Create connection
    with patch.object(FlagsmithClient, "test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = {"ok": True, "projects_count": 1}
        conn_payload = {
            "name": "Sync Target Flagsmith",
            "api_url": "https://api.flagsmith.com/api/v1",
            "token": "token-12345",
            "connection_type": "CLOUD",
            "webhook_secret": "webhook-secret-xyz",
        }
        conn_id = client.post(f"/api/v1/flagsmith/organizations/{org_id}/flagsmith/connections", json=conn_payload, headers=headers).json()["id"]

    # Mock Flagsmith API calls for sync
    with patch.object(FlagsmithClient, "get_projects", new_callable=AsyncMock) as mock_proj, \
         patch.object(FlagsmithClient, "get_project_environments", new_callable=AsyncMock) as mock_envs, \
         patch.object(FlagsmithClient, "get_project_features", new_callable=AsyncMock) as mock_feats, \
         patch.object(FlagsmithClient, "get_environment_feature_states", new_callable=AsyncMock) as mock_states:

        mock_proj.return_value = mock_flagsmith_data["projects"]
        mock_envs.return_value = mock_flagsmith_data["environments"]
        mock_feats.return_value = mock_flagsmith_data["features"]

        def mock_env_states(env_key):
            if "prod" in env_key:
                return mock_flagsmith_data["states_prod"]
            return mock_flagsmith_data["states_staging"]
        mock_states.side_effect = mock_env_states

        # 1. Trigger First Synchronization Run
        res_sync1 = client.post(f"/api/v1/flagsmith/organizations/{org_id}/flagsmith/connections/{conn_id}/sync", headers=headers)
        assert res_sync1.status_code == 200
        sync1_data = res_sync1.json()
        assert sync1_data["status"] == "COMPLETED"
        assert sync1_data["records_created"] > 0
        initial_created = sync1_data["records_created"]

        # 2. Trigger Second Synchronization Run (No remote changes) -> Idempotency verification!
        res_sync2 = client.post(f"/api/v1/flagsmith/organizations/{org_id}/flagsmith/connections/{conn_id}/sync", headers=headers)
        assert res_sync2.status_code == 200
        sync2_data = res_sync2.json()
        assert sync2_data["status"] == "COMPLETED"
        # Since remote data did not change, records_created MUST be 0! No duplicate flags!
        assert sync2_data["records_created"] == 0
        assert sync2_data["records_unchanged"] > 0

    # 3. Query Synchronized Flags
    res_flags = client.get(f"/api/v1/flagsmith/organizations/{org_id}/flags", headers=headers)
    assert res_flags.status_code == 200
    flags = res_flags.json()
    assert len(flags) == 2
    flag_keys = [f["key"] for f in flags]
    assert "checkout_v2_redesign" in flag_keys
    assert "instant_refunds" in flag_keys

    # Check that checkout_v2_redesign has both environment states
    checkout_flag = next(f for f in flags if f["key"] == "checkout_v2_redesign")
    assert len(checkout_flag["states"]) == 2
    prod_state = next(s for s in checkout_flag["states"] if s["is_production"])
    staging_state = next(s for s in checkout_flag["states"] if not s["is_production"])
    assert prod_state["enabled"] is False
    assert staging_state["enabled"] is True

    # 4. Search filter test
    res_search = client.get(f"/api/v1/flagsmith/organizations/{org_id}/flags?query=refunds", headers=headers)
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["key"] == "instant_refunds"


def test_webhook_signature_verification_and_processing(client, mock_flagsmith_data):
    # Setup user, org, connection with webhook_secret
    client.post("/api/v1/auth/register", json={"email": "webhook.user@flagforge.io", "password": "Password123!", "full_name": "Webhook User"})
    token = client.post("/api/v1/auth/login", json={"email": "webhook.user@flagforge.io", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post("/api/v1/organizations", json={"name": "Webhook Org"}, headers=headers).json()["id"]

    webhook_secret = "test-secret-hmac-key-42"
    with patch.object(FlagsmithClient, "test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = {"ok": True, "projects_count": 1}
        conn_payload = {
            "name": "Webhook Connected Flagsmith",
            "api_url": "https://api.flagsmith.com/api/v1",
            "token": "token-12345",
            "connection_type": "CLOUD",
            "webhook_secret": webhook_secret,
        }
        conn_id = client.post(f"/api/v1/flagsmith/organizations/{org_id}/flagsmith/connections", json=conn_payload, headers=headers).json()["id"]

    # Payload
    payload_dict = {
        "event_type": "FLAG_UPDATED",
        "data": {"feature_name": "checkout_v2_redesign", "enabled": True},
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")

    # 1. Reject invalid signature
    bad_headers = {"X-Flagsmith-Signature": "sha256=invalid_hash_signature", "Content-Type": "application/json"}
    res_bad = client.post(f"/api/v1/webhooks/flagsmith/{conn_id}", content=payload_bytes, headers=bad_headers)
    assert res_bad.status_code == 400
    assert "Invalid webhook signature" in res_bad.json()["detail"]

    # 2. Accept valid signature and trigger sync
    valid_sig = hmac.new(webhook_secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    good_headers = {"X-Flagsmith-Signature": f"sha256={valid_sig}", "Content-Type": "application/json"}

    with patch.object(FlagsmithClient, "get_projects", new_callable=AsyncMock) as mock_proj, \
         patch.object(FlagsmithClient, "get_project_environments", new_callable=AsyncMock) as mock_envs, \
         patch.object(FlagsmithClient, "get_project_features", new_callable=AsyncMock) as mock_feats, \
         patch.object(FlagsmithClient, "get_environment_feature_states", new_callable=AsyncMock) as mock_states:

        mock_proj.return_value = mock_flagsmith_data["projects"]
        mock_envs.return_value = mock_flagsmith_data["environments"]
        mock_feats.return_value = mock_flagsmith_data["features"]
        mock_states.return_value = []

        res_good = client.post(f"/api/v1/webhooks/flagsmith/{conn_id}", content=payload_bytes, headers=good_headers)
        assert res_good.status_code == 200
        assert res_good.json()["ok"] is True
        assert "synchronization triggered" in res_good.json()["message"]

        # 3. Replay Protection: identical webhook signature must be deduplicated
        res_replay = client.post(f"/api/v1/webhooks/flagsmith/{conn_id}", content=payload_bytes, headers=good_headers)
        assert res_replay.status_code == 200
        assert res_replay.json()["ok"] is True
        assert "replay prevention" in res_replay.json()["message"]
