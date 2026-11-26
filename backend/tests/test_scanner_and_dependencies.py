import pytest
from conftest import TestingSessionLocal
from app.services.scanner import CodeScanner
from app.services.dependency_engine import DependencyEngine
from app.models.dependency_intelligence import DependencyEdge


def test_dependency_edge_node_columns_share_the_postgres_enum():
    source_type = DependencyEdge.__table__.c.source_type.type
    target_type = DependencyEdge.__table__.c.target_type.type

    assert source_type.name == "nodetype"
    assert target_type.name == source_type.name


def test_code_scanner_and_dependency_graph(client):
    # 1. Register & login
    client.post("/api/v1/auth/register", json={"email": "scanner.dev@flagforge.io", "password": "Password123!", "full_name": "Scanner Dev"})
    token = client.post("/api/v1/auth/login", json={"email": "scanner.dev@flagforge.io", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create organization
    res_org = client.post("/api/v1/organizations", json={"name": "Scanner Org"}, headers=headers)
    org_id = res_org.json()["id"]

    # 3. Create repository
    repo_payload = {
        "name": "web-storefront",
        "repo_url": "https://github.com/cloudcorp/web-storefront",
        "default_branch": "main",
        "language": "typescript",
    }
    res_repo = client.post(f"/api/v1/organizations/{org_id}/repositories", json=repo_payload, headers=headers)
    assert res_repo.status_code == 201
    repo_id = res_repo.json()["id"]

    # 4. Trigger Scan with Python and TS snippets
    custom_code = {
        "backend/services/billing.py": """
def charge_card(user_id, amount):
    if flagsmith.has_feature("instant_refunds"):
        return process_fast(amount)
    return process_standard(amount)
        """,
        "frontend/src/Checkout.tsx": """
export function Checkout() {
    const isV2 = flagsmith.hasFeature("checkout_v2_redesign");
    const isAlsoV2 = flagsmith.hasFeature("checkout_v2_redesign");
    return isV2 ? <ModernView /> : <LegacyView />;
}
        """,
    }
    res_scan = client.post(
        f"/api/v1/organizations/{org_id}/repositories/{repo_id}/scan",
        json={"commit_sha": "abc1234", "branch": "main", "custom_files": custom_code},
        headers=headers,
    )
    assert res_scan.status_code == 200
    scan_data = res_scan.json()
    assert scan_data["status"] == "COMPLETED"
    assert scan_data["findings_count"] == 3
    assert scan_data["files_scanned"] == 2

    # 5. List flag references
    res_refs = client.get(f"/api/v1/organizations/{org_id}/flag-references", headers=headers)
    assert res_refs.status_code == 200
    refs = res_refs.json()
    assert len(refs) == 3
    found_keys = [r["flag_key"] for r in refs]
    assert "instant_refunds" in found_keys
    assert "checkout_v2_redesign" in found_keys

    # 6. Query dependency graph & blast radius
    # Match the production session configuration, where autoflush is disabled.
    TestingSessionLocal.configure(autoflush=False)
    try:
        res_graph = client.get(f"/api/v1/organizations/{org_id}/graph", headers=headers)
    finally:
        TestingSessionLocal.configure(autoflush=True)
    assert res_graph.status_code == 200
    graph = res_graph.json()
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0
    assert len({(edge["source"], edge["target"]) for edge in graph["edges"]}) == len(graph["edges"])

    res_blast = client.get(f"/api/v1/organizations/{org_id}/graph/blast-radius?flag_key=instant_refunds", headers=headers)
    assert res_blast.status_code == 200
    blast = res_blast.json()
    assert blast["flag_key"] == "instant_refunds"
    assert blast["impact_score"] > 0
