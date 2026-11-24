import time
import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.crypto import encrypt_secret, decrypt_secret
from app.core.ssrf import validate_target_url, SSRFValidationError
from app.models.organization import OrganizationMember, OrgRole
from app.models.project import Project
from app.models.environment import Environment
from app.models.flagsmith import (
    FlagsmithConnection,
    FlagsmithConnectionStatus,
    SyncHistory,
    SyncTrigger,
)
from app.models.feature_flag import FeatureFlag, FeatureFlagState
from app.schemas.flagsmith import (
    FlagsmithConnectionCreate,
    FlagsmithConnectionUpdate,
    FlagsmithConnectionOut,
    FlagsmithTestConnectionRequest,
    FlagsmithTestConnectionResponse,
    SyncHistoryOut,
    FeatureFlagOut,
    FeatureFlagStateOut,
)
from app.services.flagsmith_client import FlagsmithClient, FlagsmithApiError
from app.services.flagsmith_sync import FlagsmithSyncEngine
from app.api.deps import (
    require_org_member,
    require_org_admin,
)

router = APIRouter()


@router.post("/test", response_model=FlagsmithTestConnectionResponse)
async def test_flagsmith_connection(
    request: FlagsmithTestConnectionRequest,
):
    """Tests Flagsmith instance reachability and credential validity before saving."""
    try:
        # Validate URL against SSRF
        validate_target_url(request.api_url)
    except SSRFValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    t0 = time.perf_counter()
    client = FlagsmithClient(base_url=request.api_url, token=request.token)

    try:
        result = await client.test_connection()
        latency = round((time.perf_counter() - t0) * 1000, 2)
        return FlagsmithTestConnectionResponse(
            ok=True,
            message="Successfully verified Flagsmith connection and token.",
            projects_count=result.get("projects_count", 0),
            latency_ms=latency,
        )
    except FlagsmithApiError as e:
        latency = round((time.perf_counter() - t0) * 1000, 2)
        return FlagsmithTestConnectionResponse(
            ok=False,
            message=str(e),
            projects_count=0,
            latency_ms=latency,
        )


@router.get("/organizations/{org_id}/flagsmith/connections", response_model=List[FlagsmithConnectionOut])
async def list_connections(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lists Flagsmith connections for the specified organization."""
    stmt = (
        select(FlagsmithConnection)
        .where(FlagsmithConnection.organization_id == org_id)
        .order_by(FlagsmithConnection.created_at.desc())
    )
    connections = (await db.execute(stmt)).scalars().all()

    return [
        FlagsmithConnectionOut(
            id=c.id,
            organization_id=c.organization_id,
            name=c.name,
            api_url=c.api_url,
            connection_type=c.connection_type,
            status=c.status,
            has_token=bool(c.encrypted_token),
            has_webhook_secret=bool(c.webhook_secret),
            last_synced_at=c.last_synced_at,
            last_error=c.last_error,
            created_at=c.created_at,
        )
        for c in connections
    ]


@router.post("/organizations/{org_id}/flagsmith/connections", response_model=FlagsmithConnectionOut, status_code=status.HTTP_201_CREATED)
async def create_connection(
    org_id: uuid.UUID,
    conn_in: FlagsmithConnectionCreate,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    """Creates a Flagsmith connection, encrypts credentials, tests API, and triggers initial sync."""
    try:
        validate_target_url(conn_in.api_url)
    except SSRFValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Test credentials first
    client = FlagsmithClient(base_url=conn_in.api_url, token=conn_in.token)
    try:
        await client.test_connection()
        initial_status = FlagsmithConnectionStatus.CONNECTED
        initial_error = None
    except Exception as e:
        initial_status = FlagsmithConnectionStatus.ERROR
        initial_error = str(e)

    encrypted_token = encrypt_secret(conn_in.token)

    connection = FlagsmithConnection(
        organization_id=org_id,
        name=conn_in.name.strip(),
        api_url=conn_in.api_url.strip(),
        encrypted_token=encrypted_token,
        connection_type=conn_in.connection_type,
        status=initial_status,
        webhook_secret=conn_in.webhook_secret.strip() if conn_in.webhook_secret else None,
        last_error=initial_error,
    )
    db.add(connection)
    await db.commit()
    await db.refresh(connection)

    return FlagsmithConnectionOut(
        id=connection.id,
        organization_id=connection.organization_id,
        name=connection.name,
        api_url=connection.api_url,
        connection_type=connection.connection_type,
        status=connection.status,
        has_token=True,
        has_webhook_secret=bool(connection.webhook_secret),
        last_synced_at=connection.last_synced_at,
        last_error=connection.last_error,
        created_at=connection.created_at,
    )


@router.get("/organizations/{org_id}/flagsmith/connections/{conn_id}", response_model=FlagsmithConnectionOut)
async def get_connection(
    org_id: uuid.UUID,
    conn_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieves connection details."""
    stmt = select(FlagsmithConnection).where(
        FlagsmithConnection.id == conn_id,
        FlagsmithConnection.organization_id == org_id,
    )
    connection = (await db.execute(stmt)).scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Flagsmith connection not found in this organization")

    return FlagsmithConnectionOut(
        id=connection.id,
        organization_id=connection.organization_id,
        name=connection.name,
        api_url=connection.api_url,
        connection_type=connection.connection_type,
        status=connection.status,
        has_token=bool(connection.encrypted_token),
        has_webhook_secret=bool(connection.webhook_secret),
        last_synced_at=connection.last_synced_at,
        last_error=connection.last_error,
        created_at=connection.created_at,
    )


@router.put("/organizations/{org_id}/flagsmith/connections/{conn_id}", response_model=FlagsmithConnectionOut)
async def update_connection(
    org_id: uuid.UUID,
    conn_id: uuid.UUID,
    conn_in: FlagsmithConnectionUpdate,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Updates connection parameters or rotates API credentials."""
    stmt = select(FlagsmithConnection).where(
        FlagsmithConnection.id == conn_id,
        FlagsmithConnection.organization_id == org_id,
    )
    connection = (await db.execute(stmt)).scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Flagsmith connection not found in this organization")

    if conn_in.name is not None:
        connection.name = conn_in.name.strip()
    if conn_in.api_url is not None:
        validate_target_url(conn_in.api_url)
        connection.api_url = conn_in.api_url.strip()
    if conn_in.token is not None:
        connection.encrypted_token = encrypt_secret(conn_in.token)
    if conn_in.webhook_secret is not None:
        connection.webhook_secret = conn_in.webhook_secret.strip() if conn_in.webhook_secret else None

    await db.commit()
    await db.refresh(connection)

    return FlagsmithConnectionOut(
        id=connection.id,
        organization_id=connection.organization_id,
        name=connection.name,
        api_url=connection.api_url,
        connection_type=connection.connection_type,
        status=connection.status,
        has_token=bool(connection.encrypted_token),
        has_webhook_secret=bool(connection.webhook_secret),
        last_synced_at=connection.last_synced_at,
        last_error=connection.last_error,
        created_at=connection.created_at,
    )


@router.delete("/organizations/{org_id}/flagsmith/connections/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    org_id: uuid.UUID,
    conn_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Disconnects and deletes a Flagsmith connection."""
    stmt = select(FlagsmithConnection).where(
        FlagsmithConnection.id == conn_id,
        FlagsmithConnection.organization_id == org_id,
    )
    connection = (await db.execute(stmt)).scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Flagsmith connection not found in this organization")

    await db.delete(connection)
    await db.commit()
    return None


@router.post("/organizations/{org_id}/flagsmith/connections/{conn_id}/test", response_model=FlagsmithTestConnectionResponse)
async def test_saved_connection(
    org_id: uuid.UUID,
    conn_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Tests reachability and credentials for an existing saved connection."""
    stmt = select(FlagsmithConnection).where(
        FlagsmithConnection.id == conn_id,
        FlagsmithConnection.organization_id == org_id,
    )
    connection = (await db.execute(stmt)).scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Flagsmith connection not found")

    t0 = time.perf_counter()
    token = decrypt_secret(connection.encrypted_token)
    client = FlagsmithClient(base_url=connection.api_url, token=token)

    try:
        result = await client.test_connection()
        latency = round((time.perf_counter() - t0) * 1000, 2)
        connection.status = FlagsmithConnectionStatus.CONNECTED
        connection.last_error = None
        await db.commit()
        return FlagsmithTestConnectionResponse(
            ok=True,
            message="Connection verified successfully.",
            projects_count=result.get("projects_count", 0),
            latency_ms=latency,
        )
    except Exception as e:
        latency = round((time.perf_counter() - t0) * 1000, 2)
        connection.status = FlagsmithConnectionStatus.ERROR
        connection.last_error = str(e)
        await db.commit()
        return FlagsmithTestConnectionResponse(
            ok=False,
            message=str(e),
            projects_count=0,
            latency_ms=latency,
        )


@router.post("/organizations/{org_id}/flagsmith/connections/{conn_id}/sync", response_model=SyncHistoryOut)
async def trigger_synchronization(
    org_id: uuid.UUID,
    conn_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Triggers immediate synchronization of remote Flagsmith projects, environments, flags, and states."""
    stmt = select(FlagsmithConnection).where(
        FlagsmithConnection.id == conn_id,
        FlagsmithConnection.organization_id == org_id,
    )
    connection = (await db.execute(stmt)).scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Flagsmith connection not found in this organization")

    sync_engine = FlagsmithSyncEngine(db=db, connection=connection)
    history = await sync_engine.run_sync(trigger=SyncTrigger.MANUAL)
    return history


@router.get("/organizations/{org_id}/flagsmith/connections/{conn_id}/history", response_model=List[SyncHistoryOut])
async def list_sync_history(
    org_id: uuid.UUID,
    conn_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lists past synchronization runs for a connection."""
    stmt = (
        select(SyncHistory)
        .where(
            SyncHistory.connection_id == conn_id,
            SyncHistory.organization_id == org_id,
        )
        .order_by(desc(SyncHistory.started_at))
        .limit(50)
    )
    histories = (await db.execute(stmt)).scalars().all()
    return histories


@router.get("/organizations/{org_id}/flags", response_model=List[FeatureFlagOut])
async def list_organization_flags(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    query: Optional[str] = Query(None, description="Search flag key, name, or description"),
    project_id: Optional[uuid.UUID] = Query(None, description="Filter by project"),
):
    """Lists synchronized feature flags across projects belonging to the organization."""
    # Find all project IDs belonging to this organization
    stmt_proj = select(Project).where(Project.organization_id == org_id)
    if project_id:
        stmt_proj = stmt_proj.where(Project.id == project_id)
    projects = (await db.execute(stmt_proj)).scalars().all()
    project_map = {p.id: p.name for p in projects}

    if not project_map:
        return []

    # Query feature flags
    stmt_flags = (
        select(FeatureFlag)
        .options(
            selectinload(FeatureFlag.states).selectinload(FeatureFlagState.environment)
        )
        .where(FeatureFlag.project_id.in_(list(project_map.keys())))
        .order_by(FeatureFlag.name.asc())
    )

    if query:
        search_filter = f"%{query.strip()}%"
        stmt_flags = stmt_flags.where(
            (FeatureFlag.name.ilike(search_filter)) | (FeatureFlag.key.ilike(search_filter)) | (FeatureFlag.description.ilike(search_filter))
        )

    flags = (await db.execute(stmt_flags)).scalars().all()

    results = []
    for f in flags:
        states_out = [
            FeatureFlagStateOut(
                id=s.id,
                environment_id=s.environment_id,
                environment_name=s.environment.name if s.environment else "Unknown",
                is_production=s.environment.is_production if s.environment else False,
                enabled=s.enabled,
                value=s.value,
            )
            for s in f.states
        ]
        results.append(
            FeatureFlagOut(
                id=f.id,
                project_id=f.project_id,
                project_name=project_map.get(f.project_id, "Unknown"),
                flagsmith_feature_id=f.flagsmith_feature_id,
                name=f.name,
                key=f.key,
                description=f.description,
                type=f.type,
                default_enabled=f.default_enabled,
                is_archived=f.is_archived,
                states=states_out,
                updated_at=f.updated_at,
            )
        )
    return results
