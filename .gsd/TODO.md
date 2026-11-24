# TODO.md — Active Task List

## Phase 1: Monorepo Foundation & Dev Environment (✅ Complete)
- [x] Scaffold monorepo directory structure
- [x] Create docker-compose.yml with 7 services and healthchecks
- [x] Create .env.example with documented configuration
- [x] Create backend tests and verify /health and /healthz endpoints

## Phase 2: Application Core (✅ Complete)
- [x] Database Architecture: SQLAlchemy 2 async engine, pooling, base models, UUIDs, UTC timestamps
- [x] Core Models: User, Organization, OrganizationMember (roles: OWNER, ADMIN, DEVELOPER, VIEWER), Project, Environment
- [x] Alembic migrations setup and initial schema migration
- [x] Authentication: Password hashing (bcrypt), JWT access/refresh tokens, registration, login, logout, refresh
- [x] Organization Management: CRUD, member invites, role-based access control
- [x] Project Management: CRUD scoped to organization, multi-environment support (Production, Staging, Dev)
- [x] Tenant Isolation: Strict query scoping, cross-organization protection with automated tests
- [x] Frontend Integration: Login, Register, Org creation/selection, Project listing/creation/settings, Member management
- [x] Verification: Full pytest suite for auth, tenancy, project CRUD, and schema migrations

## Phase 3: Flagsmith Integration & Synchronizer (✅ Complete)
- [x] Flagsmith Management API adapter (Cloud and self-hosted support)
- [x] Secret credential encryption at rest with Fernet
- [x] SSRF protection blocking loopbacks and cloud metadata endpoints
- [x] Project, environment, and feature-flag synchronization with diff tracking
- [x] Feature flag state snapshot per environment (Production locked, Staging, Dev)
- [x] Secure webhook signature validation (HMAC-SHA256) & async processing
- [x] Frontend management screens: Integrations (`/integrations`), Feature Flags Explorer (`/flags`), and live Mission Control Overview (`/`)
- [x] Automated test suite verifying connection lifecycle, SSRF defense, idempotent sync, and webhook processing

## Phase 4: Code Intelligence & Static AST Scanner (🔄 Next)
