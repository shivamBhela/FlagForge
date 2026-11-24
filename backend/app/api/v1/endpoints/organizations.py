import re
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.schemas.organization import (
    OrgCreate,
    OrgOut,
    OrgMemberAdd,
    OrgMemberOut,
)
from app.api.deps import (
    get_current_user,
    require_org_member,
    require_org_admin,
)

router = APIRouter()


def slugify(text: str) -> str:
    """Converts a string to a clean URL-friendly slug."""
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", text)


@router.get("", response_model=List[OrgOut])
async def list_user_organizations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lists all organizations where the current user is an active member."""
    stmt = (
        select(Organization, OrganizationMember.role)
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == current_user.id)
        .order_by(Organization.name.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    orgs = []
    for org, role in rows:
        org_out = OrgOut(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
            role=role,
        )
        orgs.append(org_out)
    return orgs


@router.post("", response_model=OrgOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrgCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Creates a new organization and grants OWNER role to the creator."""
    base_slug = org_in.slug or slugify(org_in.name)
    slug = base_slug

    # Ensure unique slug
    counter = 1
    while True:
        stmt = select(Organization).where(Organization.slug == slug)
        exists = (await db.execute(stmt)).scalar_one_or_none()
        if not exists:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(name=org_in.name.strip(), slug=slug)
    db.add(org)
    await db.flush()

    membership = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=OrgRole.OWNER,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(org)

    return OrgOut(
        id=org.id,
        name=org.name,
        slug=org.slug,
        created_at=org.created_at,
        role=OrgRole.OWNER,
    )


@router.get("/{org_id}", response_model=OrgOut)
async def get_organization(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Gets details of an organization (requires membership)."""
    stmt = select(Organization).where(Organization.id == org_id)
    org = (await db.execute(stmt)).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrgOut(
        id=org.id,
        name=org.name,
        slug=org.slug,
        created_at=org.created_at,
        role=membership.role,
    )


@router.get("/{org_id}/members", response_model=List[OrgMemberOut])
async def list_organization_members(
    org_id: uuid.UUID,
    membership: Annotated[OrganizationMember, Depends(require_org_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lists all members of the organization."""
    stmt = (
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.organization_id == org_id)
        .order_by(OrganizationMember.created_at.asc())
    )
    members = (await db.execute(stmt)).scalars().all()

    return [
        OrgMemberOut(
            id=m.id,
            user_id=m.user_id,
            email=m.user.email,
            full_name=m.user.full_name,
            role=m.role,
            created_at=m.created_at,
        )
        for m in members
    ]


@router.post("/{org_id}/members", response_model=OrgMemberOut, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    org_id: uuid.UUID,
    member_in: OrgMemberAdd,
    membership: Annotated[OrganizationMember, Depends(require_org_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Adds an existing user to the organization with a designated role (Admin/Owner only)."""
    stmt = select(User).where(User.email == member_in.email.lower().strip())
    user_to_add = (await db.execute(stmt)).scalar_one_or_none()

    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found. User must register first.",
        )

    # Check if already a member
    stmt = select(OrganizationMember).where(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == user_to_add.id,
    )
    existing_member = (await db.execute(stmt)).scalar_one_or_none()
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization",
        )

    new_member = OrganizationMember(
        organization_id=org_id,
        user_id=user_to_add.id,
        role=member_in.role,
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return OrgMemberOut(
        id=new_member.id,
        user_id=user_to_add.id,
        email=user_to_add.email,
        full_name=user_to_add.full_name,
        role=new_member.role,
        created_at=new_member.created_at,
    )
