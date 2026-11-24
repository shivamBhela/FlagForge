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

### [DECISION-005] Credential Encryption and SSRF Defense
**Date**: 2026-11-24
**Status**: Accepted

#### Context
Management API tokens grant full administrative control over Flagsmith projects and feature flag definitions. Storing them in plaintext or accepting arbitrary user-supplied URLs creates severe security vulnerabilities, including AWS/GCP instance metadata exfiltration.

#### Decision
Use cryptography's Fernet symmetric encryption with environment-configured `ENCRYPTION_KEY` for all tokens stored at rest. Implement strict URL parsing and IP resolution in `app/core/ssrf.py`, blocking cloud metadata endpoints (`169.254.169.254`), loopbacks, RFC 1918 private subnets, and non-HTTP(S) schemes. Strip credentials from all API schemas, logs, and frontend payloads.

---

### [DECISION-006] Idempotent Database Synchronization Engine
**Date**: 2026-11-24
**Status**: Accepted

#### Context
Flagsmith synchronization jobs can be triggered manually, by webhooks, or on schedules. Multiple sync executions must never duplicate projects, environments, or flags, and must track precise change counts.

#### Decision
Implement `FlagsmithSyncEngine` using compound unique constraints and database lookup queries scoped to the tenant organization. For each sync run, calculate diffs (`records_created`, `records_updated`, `records_unchanged`, `records_deleted`) and persist an audit trail in `sync_history`. Prevent concurrent runs on the same connection.

---

### [DECISION-007] Deterministic Risk Scoring Formula
**Date**: 2026-11-24
**Status**: Accepted

#### Context
Safety and rollback decisions must be deterministic, auditable, and mathematically reproducible. AI models must never directly authorize or execute automated rollback actions.

#### Decision
Implement `DeterministicRiskEngine` calculating:
`risk = 0.30*dependency_impact + 0.25*error_anomaly + 0.20*latency_anomaly + 0.15*change_criticality + 0.10*rollout_velocity`
Combine with hard threshold checks (max error rate 5%, p95 latency 500ms). When telemetry sample size is insufficient, flag `insufficient_data` or apply explicit conservative policy.

---

### [DECISION-008] Chaos Lab Guaranteed Snapshot & Restoration
**Date**: 2026-11-24
**Status**: Accepted

#### Context
Chaos simulations in staging must never leave residual corrupt flag states or pollute downstream environments.

#### Decision
In `ChaosLabEngine`, capture a pre-change state snapshot before any mutation. Enforce a `finally` compensation block that restores the exact pre-snapshot state and performs read-after-write verification, marking `restored_verified = True`.



---

*Last updated: 2026-11-24*
