import uuid
from typing import Annotated
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.code_intelligence import Repository
from app.models.chaos import SimulationScenario
from app.models.guardian import RolloutPolicy, PolicyMode
from app.services.scanner import CodeScanner
from app.services.dependency_engine import DependencyEngine
from app.services.telemetry_pipeline import TelemetryPipeline
from app.api.deps import require_org_member

router = APIRouter()


@router.post("/organizations/{org_id}/seed-demo")
async def seed_demo_data(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Populates synthetic local fixtures; it does not connect to external providers."""
    # 1. Create Project & Feature Flags
    from app.models.project import Project
    from app.models.feature_flag import FeatureFlag, FeatureFlagType

    existing_project = (await db.execute(
        select(Project).where(
            Project.organization_id == org_id,
            Project.slug == "storefront-app",
        )
    )).scalar_one_or_none()
    if existing_project:
        return {
            "ok": True,
            "demo": True,
            "already_seeded": True,
            "message": "Synthetic demo fixtures already exist; no duplicate data was created.",
        }

    proj = Project(
        organization_id=org_id,
        name="Storefront App",
        slug="storefront-app",
        description="Synthetic demo e-commerce storefront; not linked to Flagsmith or GitHub.",
    )
    db.add(proj)
    await db.flush()

    flag1 = FeatureFlag(
        project_id=proj.id,
        name="checkout_v2_redesign",
        key="checkout_v2_redesign",
        description="Checkout redesign flag",
        type=FeatureFlagType.FLAG,
        default_enabled=True,
    )
    flag2 = FeatureFlag(
        project_id=proj.id,
        name="instant_refunds",
        key="instant_refunds",
        description="Instant refunds approval",
        type=FeatureFlagType.FLAG,
        default_enabled=True,
    )
    db.add_all([flag1, flag2])

    # 2. Create Repository
    repo = Repository(
        organization_id=org_id,
        project_id=proj.id,
        name="web-storefront",
        repo_url="https://example.invalid/flagforge/demo-web-storefront",
        default_branch="main",
        language="typescript",
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    # 2. Run initial code scan with explicit synthetic demo fixtures
    demo_code = {
        "src/components/Checkout.tsx": """
            import React from 'react';
            import { useFlags } from 'flagsmith/react';

            export function CheckoutView() {
              const flags = useFlags(["checkout_v2_redesign", "instant_refunds"]);
              const isV2 = flagsmith.hasFeature("checkout_v2_redesign");

              if (isV2) {
                return <ModernCheckout flow="v2" />;
              }
              return <LegacyCheckout />;
            }
        """,
        "backend/services/payment.py": """
            from flagsmith import Flagsmith

            def process_payment(amount, user_id):
                if flagsmith.has_feature("instant_refunds"):
                    return approve_instant_refund(amount)
                if flagsmith.is_feature_enabled("stripe_payment_element"):
                    return execute_stripe_flow(amount)
                return fallback_charge(amount)
        """,
        "src/api/recommendations.ts": """
            export async function getRecommendations(userId: string) {
              if (isFeatureEnabled("recommendations_ai_engine")) {
                return fetchAiRecs(userId);
              }
              return fetchRuleBasedRecs(userId);
            }
        """,
    }
    scanner = CodeScanner(db=db, organization_id=org_id)
    await scanner.execute_scan(repository_id=repo.id, custom_files=demo_code)

    # 3. Build dependency graph
    dep_engine = DependencyEngine(db=db, organization_id=org_id)
    await dep_engine.build_inferred_graph_from_references()

    # 4. Create Chaos scenario
    scen = SimulationScenario(
        organization_id=org_id,
        name="Checkout V2 Redesign Failure Inversion",
        target_flag_key="checkout_v2_redesign",
        description="Simulate upstream cart failure in staging with guaranteed snapshot compensation.",
        environment_name="staging",
        scenario_type="CASCADE_FAILURE",
        test_traffic_rate=150,
        duration_seconds=15,
    )
    db.add(scen)

    # 5. Seed Telemetry batch
    pipeline = TelemetryPipeline(db=db, organization_id=org_id)
    await pipeline.record_metrics_batch([
        {
            "service_name": "web-storefront",
            "environment_name": "production",
            "feature_flag_key": "checkout_v2_redesign",
            "request_count": 1250,
            "error_count": 18,
            "error_rate": 0.014,
            "p50_ms": 65.0,
            "p95_ms": 142.0,
            "p99_ms": 280.0,
        },
        {
            "service_name": "api-service",
            "environment_name": "production",
            "feature_flag_key": "instant_refunds",
            "request_count": 480,
            "error_count": 1,
            "error_rate": 0.002,
            "p50_ms": 32.0,
            "p95_ms": 88.0,
            "p99_ms": 150.0,
        },
    ])

    await db.commit()
    return {
        "ok": True,
        "demo": True,
        "already_seeded": False,
        "message": "Synthetic demo fixtures seeded locally. No provider data or external service was used.",
    }
