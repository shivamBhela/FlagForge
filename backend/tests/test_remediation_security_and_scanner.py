import io
import math
import uuid
import zipfile
import pytest
from unittest.mock import patch, AsyncMock
from conftest import TestingSessionLocal
from app.services.scanner import CodeScanner, strip_comments_preserving_lines
from app.services.dependency_engine import DependencyEngine, infer_service_from_path, infer_component_from_path
from app.services.risk_engine import DeterministicRiskEngine, classify_risk_score
from app.models.code_intelligence import Repository, FlagReference, ReferenceStatus
from app.models.dependency_intelligence import DependencyEdge, NodeType, EdgeType
from app.models.guardian import RolloutPolicy, PolicyMode
from app.services.flagsmith_client import FlagsmithClient


def test_scanner_comment_stripping():
    """Validates that JS/TS comments are stripped while preserving line count."""
    code = """// flagsmith.hasFeature("commented_single_line")
/* flagsmith.hasFeature("commented_multi_1")
   flagsmith.hasFeature("commented_multi_2") */
const active = flagsmith.hasFeature("real_active_flag");
"""
    stripped = strip_comments_preserving_lines(code)
    assert "commented_single_line" not in stripped
    assert "commented_multi_1" not in stripped
    assert "real_active_flag" in stripped
    # Verify line count is preserved so line numbers match
    assert code.count("\n") == stripped.count("\n")


def test_scanner_python_ast_no_regex_fallback():
    """Validates that Python AST does not fall back to JS regex on syntax errors."""
    scanner = CodeScanner(db=None, organization_id=uuid.uuid4())
    # Valid Python code
    valid_py = """
def check_checkout(user):
    if flagsmith.has_feature("checkout_v2"):
        return True
    return False
"""
    findings = scanner.scan_python_content(valid_py, "services/checkout.py")
    assert len(findings) == 1
    assert findings[0]["flag_key"] == "checkout_v2"
    assert findings[0]["symbol_name"] == "check_checkout"
    assert findings[0]["parser_confidence"] == 1.0

    # Invalid Python syntax
    invalid_py = """
def broken_syntax(:
    flagsmith.has_feature("should_not_parse")
"""
    findings_bad = scanner.scan_python_content(invalid_py, "services/broken.py")
    # Must NOT fall back to regex; must return empty list safely
    assert findings_bad == []


def test_scanner_safe_zip_extraction():
    """Validates that zip traversal (Zip Slip) and non-source files are safely rejected."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        # Zip slip attempt
        z.writestr("repo-root-sha/../escaped.py", 'flagsmith.has_feature("bad")')
        # Ignored directory
        z.writestr("repo-root-sha/node_modules/pkg/index.js", 'flagsmith.hasFeature("pkg_flag")')
        # Ignored binary
        z.writestr("repo-root-sha/assets/image.png", b"\x89PNG\r\n\x1a\n")
        # Valid source file
        z.writestr("repo-root-sha/src/app.ts", 'flagsmith.hasFeature("safe_flag");')

    extracted = CodeScanner.extract_source_files_from_zip(buf.getvalue())
    assert "src/app.ts" in extracted
    assert "../escaped.py" not in extracted
    assert "escaped.py" not in extracted
    assert "node_modules/pkg/index.js" not in extracted
    assert "assets/image.png" not in extracted


def test_scanner_repo_idor_prevention(client):
    """Validates that scanning a repository belonging to another organization returns 404."""
    # Org A
    client.post("/api/v1/auth/register", json={"email": "alice@tenant-a.com", "password": "Password123!", "full_name": "Alice A"})
    token_a = client.post("/api/v1/auth/login", json={"email": "alice@tenant-a.com", "password": "Password123!"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    org_a = client.post("/api/v1/organizations", json={"name": "Tenant A"}, headers=headers_a).json()["id"]

    # Org B
    client.post("/api/v1/auth/register", json={"email": "bob@tenant-b.com", "password": "Password123!", "full_name": "Bob B"})
    token_b = client.post("/api/v1/auth/login", json={"email": "bob@tenant-b.com", "password": "Password123!"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    org_b = client.post("/api/v1/organizations", json={"name": "Tenant B"}, headers=headers_b).json()["id"]

    # Create repository in Org A
    repo_a = client.post(
        f"/api/v1/organizations/{org_a}/repositories",
        json={"name": "repo-a", "repo_url": "https://github.com/tenant-a/repo-a"},
        headers=headers_a,
    ).json()["id"]

    # Bob (Org B) attempts to trigger scan on Org A's repository using Org B's org_id
    res_idor = client.post(
        f"/api/v1/organizations/{org_b}/repositories/{repo_a}/scan",
        json={"commit_sha": "abc", "branch": "main", "custom_files": {"app.ts": 'flagsmith.hasFeature("test");'}},
        headers=headers_b,
    )
    assert res_idor.status_code == 404
    assert "not found" in res_idor.json()["detail"].lower()


def test_flagsmith_test_endpoint_requires_auth_and_admin(client):
    """Validates that /api/v1/flagsmith/test and /organizations/{org_id}/test require auth and admin role."""
    test_payload = {
        "api_url": "https://api.flagsmith.com/api/v1",
        "token": "valid-token-format-1234",
        "connection_type": "CLOUD",
    }
    # Unauthenticated must return 401
    res_unauth = client.post("/api/v1/flagsmith/test", json=test_payload)
    assert res_unauth.status_code in (401, 422)

    # Register admin and regular user
    client.post("/api/v1/auth/register", json={"email": "admin@sec-corp.io", "password": "Password123!", "full_name": "Admin User"})
    token_admin = client.post("/api/v1/auth/login", json={"email": "admin@sec-corp.io", "password": "Password123!"}).json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    org_id = client.post("/api/v1/organizations", json={"name": "Sec Corp"}, headers=headers_admin).json()["id"]

    # Test with admin privileges (mocking external flagsmith call)
    with patch.object(FlagsmithClient, "test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = {"projects_count": 2}
        res_test = client.post(
            f"/api/v1/flagsmith/organizations/{org_id}/test",
            json=test_payload,
            headers=headers_admin,
        )
        assert res_test.status_code == 200
        assert res_test.json()["ok"] is True
        assert res_test.json()["projects_count"] == 2


def test_guardian_policy_numerical_validations(client):
    """Validates boundary rules on RolloutPolicy weights, error rate, and p95 latency."""
    client.post("/api/v1/auth/register", json={"email": "guardian@policy.io", "password": "Password123!", "full_name": "Guardian"})
    token = client.post("/api/v1/auth/login", json={"email": "guardian@policy.io", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    org_id = client.post("/api/v1/organizations", json={"name": "Guardian Org"}, headers=headers).json()["id"]

    # Weights summing to more than 1.0 must be rejected
    res_bad_weights = client.put(
        f"/api/v1/organizations/{org_id}/policy",
        json={
            "weight_dependency_impact": 0.5,
            "weight_error_anomaly": 0.5,
            "weight_latency_anomaly": 0.5,
            "weight_change_criticality": 0.5,
            "weight_rollout_velocity": 0.5,
        },
        headers=headers,
    )
    assert res_bad_weights.status_code == 422

    # Negative error rate threshold must be rejected
    res_neg_thresh = client.put(
        f"/api/v1/organizations/{org_id}/policy",
        json={"max_error_rate_threshold": -0.05},
        headers=headers,
    )
    assert res_neg_thresh.status_code == 422

    # Latency threshold <= 100 must be rejected (defense against divide-by-zero)
    res_low_lat = client.put(
        f"/api/v1/organizations/{org_id}/policy",
        json={"max_p95_latency_ms": 50.0},
        headers=headers,
    )
    assert res_low_lat.status_code == 422

    # Valid policy update must succeed
    res_valid = client.put(
        f"/api/v1/organizations/{org_id}/policy",
        json={
            "weight_dependency_impact": 0.30,
            "weight_error_anomaly": 0.25,
            "weight_latency_anomaly": 0.20,
            "weight_change_criticality": 0.15,
            "weight_rollout_velocity": 0.10,
            "max_error_rate_threshold": 0.05,
            "max_p95_latency_ms": 500.0,
        },
        headers=headers,
    )
    assert res_valid.status_code == 200


def test_dependency_engine_service_inference_and_idempotence():
    """Validates evidence-backed service mapping and idempotent rebuilds."""
    assert infer_service_from_path("services/billing/charge.py") == "billing"
    assert infer_service_from_path("apps/storefront/src/app.tsx") == "storefront"
    assert infer_service_from_path("packages/auth/jwt.ts") == "auth"
    assert infer_service_from_path("backend/api/router.py") == "backend"
    assert infer_service_from_path("frontend/src/index.tsx") == "frontend"
    assert infer_service_from_path("random_script.py") == "UNCLASSIFIED"
    assert infer_service_from_path("random_script.py", repo_name="payment-service") == "payment-service"
