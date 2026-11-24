---
phase: 2
plan: 1
wave: 1
gap_closure: false
---

# Plan 2.1: Phase 2 - Application Core (Database, Auth, Tenancy, Projects & UI)

## Objective
Establish the FlagForge application core: asynchronous SQLAlchemy 2.0 database engine with connection pooling and Alembic migrations; domain models for User, Organization, OrganizationMember (Owner, Admin, Developer, Viewer roles), Project, and Environment; secure JWT-based authentication with bcrypt hashing, token refresh, and logout; multi-tenant isolation enforcing organization-level authorization on all queries; and complete functional frontend screens for auth, organization switching, project management, and member administration.

## Context
Load these files for context:
- .gsd/SPEC.md
- .gsd/ROADMAP.md
- .gsd/REQUIREMENTS.md
- .gsd/STATE.md
- backend/app/main.py
- backend/app/core/config.py

## Tasks

<task type="auto">
  <name>Database Engine, Base Models & Alembic Migrations</name>
  <files>
    backend/app/core/database.py
    backend/app/core/security.py
    backend/app/models/base.py
    backend/app/models/user.py
    backend/app/models/organization.py
    backend/app/models/project.py
    backend/app/models/environment.py
    backend/alembic.ini
    backend/alembic/env.py
    backend/alembic/script.py.mako
    backend/alembic/versions/001_initial_schema.py
  </files>
  <action>
    Configure SQLAlchemy 2.0 async engine (with create_async_engine, async_sessionmaker, connection pooling).
    Create declarative Base with UUID primary keys and UTC timestamp mixins.
    Implement models:
    - User (id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
    - Organization (id, name, slug, created_at, updated_at)
    - OrganizationMember (id, organization_id, user_id, role enum: OWNER, ADMIN, DEVELOPER, VIEWER, created_at)
    - Project (id, organization_id, name, slug, description, flagsmith_project_id, created_at, updated_at)
    - Environment (id, project_id, name, slug, is_production, flagsmith_environment_key, created_at, updated_at)
    Add foreign key constraints, indexes, and unique constraints.
    Configure Alembic for async migrations and generate initial migration.
    AVOID: Synchronous database calls or missing foreign key cascades.
    USE: Async SQLAlchemy 2.0 with type annotations (Mapped, mapped_column) and UUID(as_uuid=True).
  </action>
  <verify>
    python -m pytest backend/tests/test_db_schema.py -v
  </verify>
  <done>
    Database tables create cleanly, foreign keys and indexes are verified, and migration schema passes.
  </done>
</task>

<task type="auto">
  <name>Auth, Organization & Project API with Tenant Isolation</name>
  <files>
    backend/app/schemas/auth.py
    backend/app/schemas/organization.py
    backend/app/schemas/project.py
    backend/app/api/deps.py
    backend/app/api/v1/endpoints/auth.py
    backend/app/api/v1/endpoints/organizations.py
    backend/app/api/v1/endpoints/projects.py
    backend/app/api/v1/router.py
    backend/tests/test_auth.py
    backend/tests/test_tenancy.py
  </files>
  <action>
    Implement Pydantic v2 schemas for auth, organizations, projects, and environments.
    Implement password hashing with passlib/bcrypt and JWT creation/verification (access and refresh tokens).
    Implement auth dependencies (get_current_user, get_current_active_user, get_current_org_membership).
    Implement endpoints:
    - POST /api/v1/auth/register, POST /api/v1/auth/login, POST /api/v1/auth/refresh, POST /api/v1/auth/logout, GET /api/v1/auth/me
    - GET /api/v1/organizations, POST /api/v1/organizations, GET /api/v1/organizations/{org_id}, POST /api/v1/organizations/{org_id}/members
    - GET /api/v1/organizations/{org_id}/projects, POST /api/v1/organizations/{org_id}/projects, GET /api/v1/organizations/{org_id}/projects/{project_id}, DELETE /api/v1/organizations/{org_id}/projects/{project_id}
    - GET /api/v1/organizations/{org_id}/projects/{project_id}/environments, POST /api/v1/organizations/{org_id}/projects/{project_id}/environments
    Enforce strict tenant isolation: every resource query must filter by organization_id verified against user's membership.
    Write thorough automated tests verifying authentication and cross-tenant rejection (403/404).
    AVOID: Trusting unverified organization_id from request params without checking membership.
    USE: Centralized auth/tenant dependency that raises 403 Forbidden on cross-tenant access.
  </action>
  <verify>
    python -m pytest backend/tests/test_auth.py backend/tests/test_tenancy.py -v
  </verify>
  <done>
    All authentication, organization, and project CRUD tests pass; cross-tenant access attempts are strictly rejected.
  </done>
</task>

<task type="auto">
  <name>Frontend Auth, Organization, Project & Member Screens</name>
  <files>
    frontend/src/lib/api.ts
    frontend/src/lib/auth-context.tsx
    frontend/src/app/login/page.tsx
    frontend/src/app/register/page.tsx
    frontend/src/app/organizations/new/page.tsx
    frontend/src/app/projects/page.tsx
    frontend/src/app/projects/new/page.tsx
    frontend/src/app/projects/[id]/page.tsx
    frontend/src/app/settings/page.tsx
    frontend/src/components/Header.tsx
  </files>
  <action>
    Build typed API client with token storage, refresh flow, and auth headers.
    Create React AuthContext providing user state, current organization, login, logout, and organization switcher.
    Build interactive UI pages adhering to the dark theme:
    - Login (/login) & Register (/register) with form validation and error alerts.
    - Create Organization (/organizations/new).
    - Project Listing (/projects) showing actual projects from backend, environments count, and creation button.
    - Create Project (/projects/new) supporting default environment generation (production, staging, dev).
    - Project Details (/projects/[id]) showing environments, settings, and metadata.
    - Member Management (/settings or /organizations/members) with role assignment (Owner, Admin, Developer, Viewer).
    Update Header with real user email, org selector dropdown, and logout button.
    AVOID: Static mock data on completed pages.
    USE: Live API integration with graceful loading states and error handling.
  </action>
  <verify>
    Test frontend compilation and component imports.
  </verify>
  <done>
    Frontend routes render with real backend integration, responsive dark layout, and auth state management.
  </done>
</task>

## Must-Haves
After all tasks complete, verify:
- [ ] Database schema migrations execute cleanly with Alembic
- [ ] Authentication (register, login, refresh, me) works end-to-end
- [ ] Organization membership RBAC (Owner, Admin, Developer, Viewer) is enforced
- [ ] Project and environment CRUD operations are scoped to organization
- [ ] Cross-tenant data isolation is empirically proven by automated tests
- [ ] Frontend screens for Auth, Projects, and Members are functional with backend API
