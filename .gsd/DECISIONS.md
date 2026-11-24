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

#### Rationale
- FastAPI offers automatic OpenAPI generation and typed schema validation.
- SQLAlchemy 2.0 async provides type-safe, asynchronous ORM capabilities with robust connection pooling.
- Python ecosystem provides native Tree-sitter bindings for AST code scanning.

---

### [DECISION-002] Frontend Architecture
**Date**: 2026-11-24
**Status**: Accepted

#### Context
FlagForge is an engineer-facing release intelligence tool requiring rich data visualization (dependency graphs, risk metrics, live telemetry timelines) and dark-mode aesthetic.

#### Decision
Use Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Lucide icons, and React Flow.

#### Rationale
- React Flow enables node/edge interactive graph visualization with custom node states.
- Next.js App Router provides clean route structuring and server/client component optimization.

---

### [DECISION-003] Multi-Tenancy and Data Isolation
**Date**: 2026-11-24
**Status**: Accepted

#### Context
FlagForge supports multiple organizations and projects. Cross-tenant leakage must be prevented.

#### Decision
Enforce `organization_id` on all top-level tenant entities with UUID primary keys and scoped query filters on every database operation.

---

*Last updated: 2026-11-24*
