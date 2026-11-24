import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.project import Project
from app.models.environment import Environment


@pytest.mark.anyio
async def test_database_schema_and_models():
    # Use in-memory SQLite async engine for fast test validation
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        # Create user
        user = User(
            email="developer@flagforge.io",
            hashed_password="hashed_secret_test",
            full_name="Alex Rivera",
        )
        session.add(user)
        await session.flush()
        assert user.id is not None
        assert user.is_active is True

        # Create organization
        org = Organization(
            name="Acme Corp",
            slug="acme-corp",
        )
        session.add(org)
        await session.flush()
        assert org.id is not None

        # Create organization membership with OWNER role
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=OrgRole.OWNER,
        )
        session.add(member)
        await session.flush()

        # Create project under organization
        project = Project(
            organization_id=org.id,
            name="FlagForge Web App",
            slug="flagforge-web",
            description="Main customer web application",
            flagsmith_project_id="12345",
        )
        session.add(project)
        await session.flush()

        # Create environments for project
        env_prod = Environment(
            project_id=project.id,
            name="Production",
            slug="production",
            is_production=True,
            flagsmith_environment_key="ser.test-prod-key",
        )
        env_staging = Environment(
            project_id=project.id,
            name="Staging",
            slug="staging",
            is_production=False,
            flagsmith_environment_key="ser.test-staging-key",
        )
        session.add_all([env_prod, env_staging])
        await session.commit()

        # Verify query and relationships
        assert project.organization_id == org.id
        assert env_prod.is_production is True
        assert env_staging.is_production is False
        assert member.role == OrgRole.OWNER

    await test_engine.dispose()
