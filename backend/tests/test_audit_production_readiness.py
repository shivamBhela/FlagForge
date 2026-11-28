import uuid
import pytest
from app.core.ssrf import validate_target_url, SSRFValidationError
from app.core.crypto import encrypt_secret, decrypt_secret
from app.services.flagsmith_client import FlagsmithClient
from app.core.config import Settings
from cryptography.fernet import Fernet


def test_production_config_rejects_known_development_secrets(monkeypatch):
    # Compose injects the live deployment secrets into the test container; this test
    # must evaluate constructor defaults independently of deployment configuration.
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("OTEL_INGEST_TOKEN", raising=False)
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(_env_file=None, APP_ENV="production")

    with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
        Settings(
            _env_file=None,
            APP_ENV="production",
            SECRET_KEY="unique-production-secret-key-with-more-than-32-chars",
        )

    production = Settings(
        _env_file=None,
        APP_ENV="production",
        SECRET_KEY="unique-production-secret-key-with-more-than-32-chars",
        ENCRYPTION_KEY=Fernet.generate_key().decode("ascii"),
        OTEL_INGEST_TOKEN="test-only-otel-ingestion-token-32-bytes",
    )
    assert production.APP_ENV == "production"


def test_ssrf_comprehensive_matrix():
    """Validates that all loopback, private, IPv6, and cloud metadata targets are rejected."""
    blocked_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.169.254/latest/api/token",
        "http://127.0.0.1:8000/admin",
        "http://localhost:3000",
        "http://[::1]:8000/api",
        "http://10.0.0.1/internal",
        "http://172.16.0.1/cluster",
        "http://192.168.1.100/router",
        "http://instance-data/latest",
        "http://metadata.google.internal/computeMetadata/v1/",
        "ftp://api.flagsmith.com/resource",
        "file:///etc/passwd",
    ]
    for url in blocked_urls:
        with pytest.raises(SSRFValidationError):
            validate_target_url(url)

    # Valid public URLs must pass
    assert validate_target_url("https://edge.api.flagsmith.com/api/v1") == "https://edge.api.flagsmith.com/api/v1"
    assert validate_target_url("https://api.flagsmith.com/api/v1") == "https://api.flagsmith.com/api/v1"


def test_crypto_tamper_detection():
    """Validates that encrypted secrets cannot be decrypted if tampered with."""
    secret = "flagsmith-secret-mgmt-key-prod-999"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert decrypt_secret(encrypted) == secret

    # Tampered ciphertext must fail decryption
    tampered = encrypted[:-4] + "AAAA"
    with pytest.raises(Exception):
        decrypt_secret(tampered)


def test_flagsmith_client_url_normalization():
    """Validates that custom Flagsmith base URLs are properly normalized to /api/v1."""
    c1 = FlagsmithClient(base_url="https://flagsmith.mycompany.internal", token="test-key")
    assert c1.base_url == "https://flagsmith.mycompany.internal/api/v1"

    c2 = FlagsmithClient(base_url="https://flagsmith.mycompany.internal/api/v1/", token="test-key")
    assert c2.base_url == "https://flagsmith.mycompany.internal/api/v1"

    c_api = FlagsmithClient(base_url="https://flagsmith.mycompany.internal/api", token="test-key")
    assert c_api.base_url == "https://flagsmith.mycompany.internal/api/v1"

    c3 = FlagsmithClient(base_url="https://edge.api.flagsmith.com/api/v1", token="test-key")
    assert c3.base_url == "https://edge.api.flagsmith.com/api/v1"


def test_rbac_and_tenant_isolation_matrix(client):
    """Empirically verifies that cross-tenant access is rejected with 403, and Viewer role cannot mutate."""
    # Register User 1 (Admin of Org 1)
    client.post("/api/v1/auth/register", json={"email": "org1.admin@corp.io", "password": "Password123!", "full_name": "Org1 Admin"})
    token1 = client.post("/api/v1/auth/login", json={"email": "org1.admin@corp.io", "password": "Password123!"}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {token1}"}
    org1_id = client.post("/api/v1/organizations", json={"name": "Org 1 Primary"}, headers=h1).json()["id"]

    # Register User 2 (Admin of Org 2)
    client.post("/api/v1/auth/register", json={"email": "org2.admin@corp.io", "password": "Password123!", "full_name": "Org2 Admin"})
    token2 = client.post("/api/v1/auth/login", json={"email": "org2.admin@corp.io", "password": "Password123!"}).json()["access_token"]
    h2 = {"Authorization": f"Bearer {token2}"}
    org2_id = client.post("/api/v1/organizations", json={"name": "Org 2 Isolated"}, headers=h2).json()["id"]

    # Register User 3 (Viewer in Org 1)
    client.post("/api/v1/auth/register", json={"email": "viewer@corp.io", "password": "Password123!", "full_name": "Org1 Viewer"})
    token3 = client.post("/api/v1/auth/login", json={"email": "viewer@corp.io", "password": "Password123!"}).json()["access_token"]
    h3 = {"Authorization": f"Bearer {token3}"}
    # Add User 3 to Org 1 as VIEWER
    res_add = client.post(f"/api/v1/organizations/{org1_id}/members", json={"email": "viewer@corp.io", "role": "VIEWER"}, headers=h1)
    assert res_add.status_code == 201

    # 1. Cross-Tenant Rejection: User 2 cannot access Org 1 data
    res_cross = client.get(f"/api/v1/organizations/{org1_id}/repositories", headers=h2)
    assert res_cross.status_code == 403

    res_cross_flags = client.get(f"/api/v1/flagsmith/organizations/{org1_id}/flags", headers=h2)
    assert res_cross_flags.status_code == 403

    res_cross_scens = client.get(f"/api/v1/organizations/{org1_id}/scenarios", headers=h2)
    assert res_cross_scens.status_code == 403

    # 2. RBAC Enforcement: Viewer in Org 1 cannot create repositories or trigger rollbacks
    res_viewer_repo = client.post(
        f"/api/v1/organizations/{org1_id}/repositories",
        json={"name": "hacked-repo", "repo_url": "https://github.com/test/repo"},
        headers=h3,
    )
    assert res_viewer_repo.status_code == 403

    res_viewer_rb = client.post(
        f"/api/v1/organizations/{org1_id}/guardian/rollback",
        json={"flag_key": "checkout_v2", "environment_name": "production"},
        headers=h3,
    )
    assert res_viewer_rb.status_code == 403

    # 3. Viewer CAN read repositories and graph
    res_viewer_read = client.get(f"/api/v1/organizations/{org1_id}/repositories", headers=h3)
    assert res_viewer_read.status_code == 200
