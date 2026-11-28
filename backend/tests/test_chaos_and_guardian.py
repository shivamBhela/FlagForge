import pytest
import asyncio
import uuid
from datetime import datetime, timedelta, timezone


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
    assert res_seed.json()["demo"] is True
    res_seed_repeat = client.post(f"/api/v1/organizations/{org_id}/seed-demo", headers=headers)
    assert res_seed_repeat.status_code == 200
    assert res_seed_repeat.json()["already_seeded"] is True

    # Same flag keys are valid in separate tenants; Chaos Lab must resolve only
    # the flag belonging to the organization that owns the scenario.
    client.post("/api/v1/auth/register", json={"email": "other.tenant@flagforge.io", "password": "Password123!", "full_name": "Other Tenant"})
    other_token = client.post("/api/v1/auth/login", json={"email": "other.tenant@flagforge.io", "password": "Password123!"}).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    other_org = client.post("/api/v1/organizations", json={"name": "Other Tenant Org"}, headers=other_headers).json()
    other_project = client.post(
        f"/api/v1/organizations/{other_org['id']}/projects",
        json={"name": "Other Tenant Project", "slug": "other-tenant-project"},
        headers=other_headers,
    ).json()

    import asyncio
    import uuid
    from conftest import TestingSessionLocal
    from app.models.feature_flag import FeatureFlag, FeatureFlagType

    async def add_same_key_to_other_tenant():
        async with TestingSessionLocal() as session:
            session.add(FeatureFlag(
                project_id=uuid.UUID(other_project["id"]),
                name="Checkout V2 from another tenant",
                key="checkout_v2_redesign",
                type=FeatureFlagType.FLAG,
                default_enabled=False,
            ))
            await session.commit()

    asyncio.run(add_same_key_to_other_tenant())

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
    assert run_data["restored_verified"] is False
    assert "no remote flag was changed" in run_data["log_output"]
    assert run_data["pre_snapshot"]["simulation_mode"] == "SYNTHETIC_NO_REMOTE_MUTATION"

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

    # Missing telemetry is uncertain, never interpreted as a healthy release.
    res_no_telemetry = client.post(
        f"/api/v1/organizations/{org_id}/guardian/evaluate?flag_key=flag_without_telemetry&environment_name=staging",
        headers=headers,
    )
    assert res_no_telemetry.status_code == 200
    no_telemetry = res_no_telemetry.json()
    assert no_telemetry["factors"]["telemetry_confidence"] == "INSUFFICIENT"
    assert no_telemetry["error_anomaly_score"] == 100.0
    assert no_telemetry["latency_anomaly_score"] == 100.0
    assert no_telemetry["recommended_action"] == "MANUAL_APPROVAL_REQUIRED"

    # Sufficient telemetry can still identify a critical release, but the
    # recommendation must never claim that the unavailable remote rollback ran.
    policy = client.put(
        f"/api/v1/organizations/{org_id}/policy",
        json={
            "weight_dependency_impact": 0.0,
            "weight_error_anomaly": 0.6,
            "weight_latency_anomaly": 0.4,
            "weight_change_criticality": 0.0,
            "weight_rollout_velocity": 0.0,
            "min_telemetry_samples": 10,
        },
        headers=headers,
    )
    assert policy.status_code == 200
    from conftest import TestingSessionLocal
    from app.models.telemetry import TelemetryAggregate

    async def record_critical_telemetry():
        async with TestingSessionLocal() as session:
            now = datetime.now(timezone.utc)
            session.add(TelemetryAggregate(
                organization_id=uuid.UUID(org_id),
                service_name="qa-risk-test",
                environment_name="production",
                feature_flag_key="critical_qa_flag",
                window_start=now - timedelta(minutes=5),
                window_end=now,
                request_count=100,
                error_count=100,
                error_rate=1.0,
                p50_ms=500.0,
                p95_ms=500.0,
                p99_ms=500.0,
                latency_bucket_bounds=[10.0, 100.0, 500.0],
                latency_bucket_counts=[0, 0, 100, 0],
            ))
            await session.commit()

    asyncio.run(record_critical_telemetry())
    critical = client.post(
        f"/api/v1/organizations/{org_id}/guardian/evaluate?flag_key=critical_qa_flag&environment_name=production",
        headers=headers,
    )
    assert critical.status_code == 200
    assert critical.json()["risk_band"] == "CRITICAL"
    assert critical.json()["factors"]["telemetry_confidence"] == "SUFFICIENT"
    assert critical.json()["factors"]["rollback_available"] is False
    assert critical.json()["recommended_action"] == "MANUAL_APPROVAL_REQUIRED"

    # 6. Release Guardian Rollback
    res_rb = client.post(
        f"/api/v1/organizations/{org_id}/guardian/rollback",
        json={"flag_key": "checkout_v2_redesign", "environment_name": "production", "reason": "Test safety breach"},
        headers=headers,
    )
    assert res_rb.status_code == 501
    assert "No change was made" in res_rb.json()["detail"]

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
    assert patch["diff_preview"] == (
        "Connect GitHub, select the authorized repository, load this exact file, "
        "and prepare a reviewable diff."
    )
    assert patch["status"] == "DRAFT"

    # 9. Chaos Lab: Interrupted run recovery verification
    from app.services.chaos_lab import ChaosLabEngine
    from app.models.chaos import SimulationRun, SimulationStatus
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
