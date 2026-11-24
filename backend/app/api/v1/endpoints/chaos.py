import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.chaos import SimulationScenario, SimulationRun
from app.services.chaos_lab import ChaosLabEngine
from app.api.deps import require_org_member, require_org_admin

router = APIRouter()


class ScenarioCreate(BaseModel):
    name: str
    target_flag_key: str
    description: Optional[str] = None
    environment_name: str = "staging"
    scenario_type: str = "TOGGLE_INVERSION"
    test_traffic_rate: int = 100
    duration_seconds: int = 15


@router.get("/organizations/{org_id}/scenarios")
async def list_scenarios(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(SimulationScenario).where(SimulationScenario.organization_id == org_id)
    scenarios = (await db.execute(stmt)).scalars().all()
    return scenarios


@router.post("/organizations/{org_id}/scenarios", status_code=status.HTTP_201_CREATED)
async def create_scenario(
    org_id: uuid.UUID,
    scen_in: ScenarioCreate,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Enforce isolation: never allow chaos against production
    if "prod" in scen_in.environment_name.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chaos Lab scenarios are strictly forbidden against production environments.",
        )

    scen = SimulationScenario(
        organization_id=org_id,
        name=scen_in.name,
        target_flag_key=scen_in.target_flag_key,
        description=scen_in.description,
        environment_name=scen_in.environment_name,
        scenario_type=scen_in.scenario_type,
        test_traffic_rate=scen_in.test_traffic_rate,
        duration_seconds=scen_in.duration_seconds,
    )
    db.add(scen)
    await db.commit()
    await db.refresh(scen)
    return scen


@router.post("/organizations/{org_id}/scenarios/{scenario_id}/run")
async def run_scenario(
    org_id: uuid.UUID,
    scenario_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = ChaosLabEngine(db=db, organization_id=org_id)
    run = await engine.run_scenario(scenario_id)
    return run


@router.get("/organizations/{org_id}/simulation-runs")
async def list_simulation_runs(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = (
        select(SimulationRun)
        .where(SimulationRun.organization_id == org_id)
        .order_by(SimulationRun.created_at.desc())
    )
    runs = (await db.execute(stmt)).scalars().all()
    return runs
