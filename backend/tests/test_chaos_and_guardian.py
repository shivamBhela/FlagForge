import pytest


def test_chaos_lab_telemetry_guardian_and_cleanup(client):
    # 1. Register & login
    client.post("/api/v1/auth/register", json={"email": "guardian.lead@flagforge.io", "password": "Password123!", "full_name": "Guardian Lead"})
    token = client.post("/api/v1/auth/login", json={"email": "guardian.lead@flagforge.io", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create organization
    res_org = client.post("/api/v1/organizations", json={"name": "Guardian Org"}, headers=headers)
    org_id = res_org.json()["id"]

    # 3. Seed complete demo data
    res_seed = client.post(f"/api/v1/organizations/{org_id}/seed-demo", headers=headers)
    assert res_seed.status_code == 200
    assert res_seed.json()["ok"] is True

    # 4. Chaos Lab: List scenarios and trigger controlled run
    res_scens = client.get(f"/api/v1/organizations/{org_id}/scenarios", headers=headers)
    assert res_scens.status_code == 200
    scenarios = res_scens.json()
    assert len(scenarios) >= 1
    scen_id = scenarios[0]["id"]

    res_run = client.post(f"/api/v1/organizations/{org_id}/scenarios/{scen_id}/run", headers=headers)
    assert res_run.status_code == 200
    run_data = res_run.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["restored_verified"] is True
    assert "State restoration VERIFIED" in run_data["log_output"]

    # 5. Deterministic Risk Evaluation
    res_risk = client.post(
        f"/api/v1/organizations/{org_id}/guardian/evaluate?flag_key=checkout_v2_redesign&environment_name=production",
        headers=headers,
    )
    assert res_risk.status_code == 200
    risk = res_risk.json()
    assert 0.0 <= risk["calculated_score"] <= 100.0
    assert risk["risk_band"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert risk["dependency_score"] >= 0.0
    assert risk["error_anomaly_score"] >= 0.0

    # 6. Release Guardian Rollback
    res_rb = client.post(
        f"/api/v1/organizations/{org_id}/guardian/rollback",
        json={"flag_key": "checkout_v2_redesign", "environment_name": "production", "reason": "Test safety breach"},
        headers=headers,
    )
    assert res_rb.status_code == 200
    rb_data = res_rb.json()
    assert rb_data["status"] == "VERIFIED"
    assert rb_data["verified_state"]["enabled"] is False

    # 7. Incident Explanation
    res_expl = client.get(
        f"/api/v1/organizations/{org_id}/incidents/explain?flag_key=checkout_v2_redesign&environment_name=production",
        headers=headers,
    )
    assert res_expl.status_code == 200
    expl = res_expl.json()
    assert "checkout_v2_redesign" in expl["summary"]
    assert len(expl["recommended_actions"]) > 0

    # 8. Cleanup Studio: List stale candidates & preview patch
    res_stale = client.get(f"/api/v1/organizations/{org_id}/cleanup/stale-flags", headers=headers)
    assert res_stale.status_code == 200
    stale_flags = res_stale.json()
    assert len(stale_flags) >= 1

    res_patch = client.post(
        f"/api/v1/organizations/{org_id}/cleanup/patches/preview",
        json={"flag_key": "checkout_v2_redesign", "file_path": "src/components/Checkout.tsx"},
        headers=headers,
    )
    assert res_patch.status_code == 200
    patch = res_patch.json()
    assert "--- a/src/components/Checkout.tsx" in patch["diff_preview"]
    assert patch["status"] == "DRAFT"

    # 9. Chaos Lab: Interrupted run recovery verification
    from app.services.chaos_lab import ChaosLabEngine
    from app.models.chaos import SimulationRun, SimulationStatus
    import uuid
    import asyncio
    from conftest import TestingSessionLocal

    async def simulate_orphaned():
        async with TestingSessionLocal() as session:
            orphaned_run = SimulationRun(
                organization_id=uuid.UUID(org_id),
                scenario_id=uuid.UUID(scen_id),
                status=SimulationStatus.RUNNING,
                pre_snapshot={"flag_key": "checkout_v2_redesign", "enabled": True},
            )
            session.add(orphaned_run)
            await session.commit()
            
            engine = ChaosLabEngine(db=session, organization_id=uuid.UUID(org_id))
            recovered = await engine.recover_interrupted_runs()
            assert recovered >= 1

    asyncio.run(simulate_orphaned())
