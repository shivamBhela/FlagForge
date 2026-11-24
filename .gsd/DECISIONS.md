# DECISIONS.md — Architecture Decision Records

> **Purpose**: Log significant technical decisions and their rationale.

---

## Decisions

### [DECISION-001] Backend Architecture and Technology Stack
**Date**: 2026-11-24
**Status**: Accepted

#### Context
FlagForge requires high-performance asynchronous API endpoints, background job coordination, real-time telemetry processing, and rock-solid database transactions.

#### Decision
Use Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (asyncio with asyncpg / aiosqlite for tests), and Alembic for database migrations.

---

### [DECISION-002] Frontend Architecture
**Date**: 2026-11-24
**Status**: Accepted

#### Context
FlagForge is an engineer-facing release intelligence tool requiring rich data visualization and dark-mode aesthetic.

#### Decision
Use Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Lucide icons, and React Flow.

---

### [DECISION-003] Multi-Tenancy and Data Isolation
**Date**: 2026-11-24
**Status**: Accepted

#### Context
FlagForge supports multiple organizations and projects. Cross-tenant leakage must be prevented.

#### Decision
Enforce `organization_id` on all top-level tenant entities with UUID primary keys and scoped query filters on every database operation. In `deps.py`, `OrgMembershipChecker` verifies tenant membership before any resource route executes.

---

### [DECISION-004] Native Bcrypt and Unique JWT Identifiers
**Date**: 2026-11-24
**Status**: Accepted

#### Context
Passlib has known compatibility bugs with `bcrypt >= 4.1` on Python 3.11+ due to internal wrap-bug detection. Additionally, sub-second token refresh needs replay prevention.

#### Decision
Use `bcrypt` directly with 72-byte truncation safety and inject unique `jti` (UUID4) into all access and refresh tokens.

---

*Last updated: 2026-11-24*
