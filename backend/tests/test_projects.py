def test_project_and_environment_lifecycle(client):
    # 1. Register and login
    client.post("/api/v1/auth/register", json={"email": "lead@flagforge.io", "password": "Password123!", "full_name": "Tech Lead"})
    token = client.post("/api/v1/auth/login", json={"email": "lead@flagforge.io", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create organization
    res_org = client.post("/api/v1/organizations", json={"name": "Stark Industries"}, headers=headers)
    assert res_org.status_code == 201
    org_id = res_org.json()["id"]

    # 3. Create project with default environments
    res_proj = client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={
            "name": "Arc Reactor Control",
            "slug": "arc-reactor",
            "description": "Critical power distribution flag configuration",
            "flagsmith_project_id": "stark-101",
            "create_default_environments": True,
        },
        headers=headers,
    )
    assert res_proj.status_code == 201
    proj = res_proj.json()
    proj_id = proj["id"]
    assert proj["name"] == "Arc Reactor Control"
    assert proj["slug"] == "arc-reactor"
    assert proj["flagsmith_project_id"] == "stark-101"
    assert len(proj["environments"]) == 3

    # Check default env names
    env_names = [e["name"] for e in proj["environments"]]
    assert "Production" in env_names
    assert "Staging" in env_names
    assert "Development" in env_names

    # 4. List projects for organization
    res_list = client.get(f"/api/v1/organizations/{org_id}/projects", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 5. Get project by ID
    res_get = client.get(f"/api/v1/organizations/{org_id}/projects/{proj_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == proj_id

    # 6. Update project
    res_update = client.put(
        f"/api/v1/organizations/{org_id}/projects/{proj_id}",
        json={"name": "Arc Reactor Control v2", "flagsmith_project_id": "stark-102"},
        headers=headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Arc Reactor Control v2"
    assert res_update.json()["flagsmith_project_id"] == "stark-102"

    # 7. Add custom environment
    res_env = client.post(
        f"/api/v1/organizations/{org_id}/projects/{proj_id}/environments",
        json={
            "name": "Disaster Recovery",
            "slug": "dr-env",
            "is_production": True,
            "flagsmith_environment_key": "ser.dr-stark-key",
        },
        headers=headers,
    )
    assert res_env.status_code == 201
    env_data = res_env.json()
    assert env_data["name"] == "Disaster Recovery"
    assert env_data["is_production"] is True
    assert env_data["flagsmith_environment_key"] == "ser.dr-stark-key"

    # 8. List environments
    res_envs = client.get(f"/api/v1/organizations/{org_id}/projects/{proj_id}/environments", headers=headers)
    assert res_envs.status_code == 200
    assert len(res_envs.json()) == 4

    # 9. Delete project
    res_del = client.delete(f"/api/v1/organizations/{org_id}/projects/{proj_id}", headers=headers)
    assert res_del.status_code == 204

    # 10. Confirm deletion
    res_check = client.get(f"/api/v1/organizations/{org_id}/projects/{proj_id}", headers=headers)
    assert res_check.status_code == 404
