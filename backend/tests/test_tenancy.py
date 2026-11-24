def test_cross_tenant_isolation_and_rbac(client):
    # 1. Register User Alpha and User Beta
    client.post("/api/v1/auth/register", json={"email": "alpha@flagforge.io", "password": "PasswordAlpha123!", "full_name": "Alpha User"})
    client.post("/api/v1/auth/register", json={"email": "beta@flagforge.io", "password": "PasswordBeta123!", "full_name": "Beta User"})

    token_alpha = client.post("/api/v1/auth/login", json={"email": "alpha@flagforge.io", "password": "PasswordAlpha123!"}).json()["access_token"]
    token_beta = client.post("/api/v1/auth/login", json={"email": "beta@flagforge.io", "password": "PasswordBeta123!"}).json()["access_token"]

    headers_alpha = {"Authorization": f"Bearer {token_alpha}"}
    headers_beta = {"Authorization": f"Bearer {token_beta}"}

    # 2. User Alpha creates Org Alpha
    res_org_a = client.post("/api/v1/organizations", json={"name": "Alpha Corp"}, headers=headers_alpha)
    assert res_org_a.status_code == 201
    org_a = res_org_a.json()
    org_a_id = org_a["id"]
    assert org_a["role"] == "OWNER"

    # 3. User Beta creates Org Beta
    res_org_b = client.post("/api/v1/organizations", json={"name": "Beta Ltd"}, headers=headers_beta)
    assert res_org_b.status_code == 201
    org_b = res_org_b.json()
    org_b_id = org_b["id"]
    assert org_b["role"] == "OWNER"

    # 4. User Alpha creates Project Alpha under Org Alpha
    res_proj_a = client.post(
        f"/api/v1/organizations/{org_a_id}/projects",
        json={"name": "Alpha Core Flag System", "description": "Flag service", "create_default_environments": True},
        headers=headers_alpha,
    )
    assert res_proj_a.status_code == 201
    proj_a = res_proj_a.json()
    proj_a_id = proj_a["id"]
    assert len(proj_a["environments"]) == 3  # Production, Staging, Development

    # 5. User Beta creates Project Beta under Org Beta
    res_proj_b = client.post(
        f"/api/v1/organizations/{org_b_id}/projects",
        json={"name": "Beta Payment Gateway", "description": "Payments", "create_default_environments": True},
        headers=headers_beta,
    )
    assert res_proj_b.status_code == 201
    proj_b = res_proj_b.json()
    proj_b_id = proj_b["id"]

    # -------------------------------------------------------------
    # TENANT ISOLATION ASSERTIONS:
    # -------------------------------------------------------------
    # User Beta attempts to list or access projects in Org Alpha -> 403 Forbidden
    res_leak_attempt = client.get(f"/api/v1/organizations/{org_a_id}/projects", headers=headers_beta)
    assert res_leak_attempt.status_code == 403
    assert "Not authorized" in res_leak_attempt.json()["detail"]

    # User Beta attempts to access specific Project A in Org Alpha -> 403 Forbidden
    res_leak_proj = client.get(f"/api/v1/organizations/{org_a_id}/projects/{proj_a_id}", headers=headers_beta)
    assert res_leak_proj.status_code == 403

    # User Alpha attempts to access Org Beta -> 403 Forbidden
    res_alpha_leak = client.get(f"/api/v1/organizations/{org_b_id}", headers=headers_alpha)
    assert res_alpha_leak.status_code == 403

    # -------------------------------------------------------------
    # RBAC & MEMBER COLLABORATION ASSERTIONS:
    # -------------------------------------------------------------
    # Alpha invites Beta into Org Alpha as DEVELOPER
    res_invite = client.post(
        f"/api/v1/organizations/{org_a_id}/members",
        json={"email": "beta@flagforge.io", "role": "DEVELOPER"},
        headers=headers_alpha,
    )
    assert res_invite.status_code == 201
    assert res_invite.json()["role"] == "DEVELOPER"

    # Now Beta can access Org Alpha projects
    res_beta_allowed = client.get(f"/api/v1/organizations/{org_a_id}/projects", headers=headers_beta)
    assert res_beta_allowed.status_code == 200
    assert len(res_beta_allowed.json()) == 1

    # But Beta (DEVELOPER) cannot delete Project Alpha (requires ADMIN or OWNER)
    res_beta_delete = client.delete(f"/api/v1/organizations/{org_a_id}/projects/{proj_a_id}", headers=headers_beta)
    assert res_beta_delete.status_code == 403
    assert "Action requires" in res_beta_delete.json()["detail"]

    # Alpha (OWNER) can delete Project Alpha
    res_alpha_delete = client.delete(f"/api/v1/organizations/{org_a_id}/projects/{proj_a_id}", headers=headers_alpha)
    assert res_alpha_delete.status_code == 204

    # Verify project is gone
    res_get_deleted = client.get(f"/api/v1/organizations/{org_a_id}/projects/{proj_a_id}", headers=headers_alpha)
    assert res_get_deleted.status_code == 404
