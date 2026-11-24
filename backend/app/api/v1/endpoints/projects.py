import re
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.organization import OrganizationMember, OrgRole
from app.models.project import Project
from app.models.environment import Environment
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    EnvironmentCreate,
    EnvironmentOut,
)
from app.api.deps import (
    require_org_member,
    require_org_admin,
)

router = APIRouter()


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", text)


@router.get("/{org_id}/projects", response_model=List[ProjectOut])
async def list_projects(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lists all projects scoped to the organization."""
    stmt = (
        select(Project)
        .options(selectinload(Project.environments))
        .where(Project.organization_id == org_id)
        .order_by(Project.created_at.desc())
    )
    projects = (await db.execute(stmt)).scalars().all()
    return projects


@router.post("/{org_id}/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    org_id: uuid.UUID,
    project_in: ProjectCreate,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Creates a project under an organization with optional default environments."""
    base_slug = project_in.slug or slugify(project_in.name)
    slug = base_slug

    # Ensure unique slug in this organization
    counter = 1
    while True:
        stmt = select(Project).where(
            Project.organization_id == org_id,
            Project.slug == slug,
        )
        exists = (await db.execute(stmt)).scalar_one_or_none()
        if not exists:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    project = Project(
        organization_id=org_id,
        name=project_in.name.strip(),
        slug=slug,
        description=project_in.description.strip(),
        flagsmith_project_id=project_in.flagsmith_project_id,
    )
    db.add(project)
    await db.flush()

    if project_in.create_default_environments:
        default_envs = [
            Environment(project_id=project.id, name="Production", slug="production", is_production=True),
            Environment(project_id=project.id, name="Staging", slug="staging", is_production=False),
            Environment(project_id=project.id, name="Development", slug="development", is_production=False),
        ]
        db.add_all(default_envs)

    await db.commit()

    # Re-fetch with environments eager-loaded
    stmt = (
        select(Project)
        .options(selectinload(Project.environments))
        .where(Project.id == project.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/{org_id}/projects/{project_id}", response_model=ProjectOut)
async def get_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Gets details of a single project scoped to org_id."""
    stmt = (
        select(Project)
        .options(selectinload(Project.environments))
        .where(Project.id == project_id, Project.organization_id == org_id)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this organization")
    return project


@router.put("/{org_id}/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Updates a project (Admin/Owner only)."""
    stmt = (
        select(Project)
        .options(selectinload(Project.environments))
        .where(Project.id == project_id, Project.organization_id == org_id)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this organization")

    if project_in.name is not None:
        project.name = project_in.name.strip()
    if project_in.description is not None:
        project.description = project_in.description.strip()
    if project_in.flagsmith_project_id is not None:
        project.flagsmith_project_id = project_in.flagsmith_project_id.strip()

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{org_id}/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Deletes a project and cascades environments (Admin/Owner only)."""
    stmt = select(Project).where(Project.id == project_id, Project.organization_id == org_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this organization")

    await db.delete(project)
    await db.commit()
    return None


@router.get("/{org_id}/projects/{project_id}/environments", response_model=List[EnvironmentOut])
async def list_environments(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lists environments for a given project."""
    # First verify project belongs to organization
    stmt = select(Project).where(Project.id == project_id, Project.organization_id == org_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this organization")

    stmt_env = (
        select(Environment)
        .where(Environment.project_id == project_id)
        .order_by(Environment.is_production.desc(), Environment.name.asc())
    )
    envs = (await db.execute(stmt_env)).scalars().all()
    return envs


@router.post("/{org_id}/projects/{project_id}/environments", response_model=EnvironmentOut, status_code=status.HTTP_201_CREATED)
async def create_environment(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    env_in: EnvironmentCreate,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Creates a new environment for a project."""
    stmt = select(Project).where(Project.id == project_id, Project.organization_id == org_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this organization")

    slug = env_in.slug or slugify(env_in.name)
    env = Environment(
        project_id=project_id,
        name=env_in.name.strip(),
        slug=slug,
        is_production=env_in.is_production,
        flagsmith_environment_key=env_in.flagsmith_environment_key,
    )
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return env
