---
milestone: "FlagForge Application Core"
version: "0.2.0"
updated: "2026-11-28"
---

# FlagForge Roadmap

> **Current Phase:** 11 - End-to-End Verification and Remaining Integrations
> **Status:** Partial based on the 2026-11-28 QA reports. Docker, migrations, backend/CLI/frontend checks and headed browser workflows passed. The latest FlagForge session has no connected Flagsmith instance; prior isolated Staging sync/webhook and telemetry ingestion results are historical. Provider rollback remains disabled, and the application cleanup-to-PR workflow is not live-verified. No public deployment exists.

## Must-Haves (from SPEC)

- [x] Monorepo workspace scaffolded with shared tooling and service boundaries
- [x] Docker Compose orchestrating all 7 services (`web`, `api`, `worker`, `postgres`, `redis`, `otel-collector`, `demo-app`)
- [x] Deep health-check endpoint (`/healthz`) on API reporting database and cache status
- [x] Automated one-command setup script for developer onboarding
- [x] Database schema migrations with Alembic and async SQLAlchemy 2.0
- [x] Multi-tenant User, Organization, Project, and Environment models with UUIDs and UTC timestamps
- [x] JWT Authentication with bcrypt hashing, token refresh, and logout
- [x] Strict tenant isolation and RBAC (Owner, Admin, Developer, Viewer) verified by automated tests
- [x] Functional frontend screens for Auth, Organization switching, Project CRUD, and Member management

---

## Phases

### Phase 1: Monorepo Scaffolding & Multi-Service Infrastructure
**Status:** ✅ Complete
**Objective:** Scaffold the monorepo architecture, configure Docker Compose with all 7 services, implement deep health-check endpoints, and provide a one-command setup script.
**Requirements:** REQ-INFRA-01, REQ-INFRA-02, REQ-INFRA-03, REQ-INFRA-04

**Plans:**
- [x] Plan 1.1: Monorepo Scaffolding, Docker Compose (7 Services), Health-Check, and Setup Script

---

### Phase 2: Application Core (Database, Auth, Tenancy, Projects & UI)
**Status:** ✅ Complete
**Objective:** Database schema migrations, async SQLAlchemy 2.0 models, JWT auth, tenant isolation, RBAC, project/env management, and frontend screens.
**Requirements:** REQ-02, NFR-02, NFR-03
**Depends on:** Phase 1

**Plans:**
- [x] Plan 2.1: Phase 2 - Application Core (Database, Auth, Tenancy, Projects & UI)

---

### Phase 3: Flagsmith Integration & Synchronizer
**Status:** 🟡 Partial — isolated Staging sync, state-change detection and signed webhook processing passed historically; the latest QA run had no connected instance and made no provider request.
**Objective:** Backend adapter for Flagsmith Management API (Cloud/self-hosted), connection tests, project/environment/flag synchronization and secure webhook handler. Historical Staging sync and signed webhook tests passed; current live connectivity was not reverified in the latest QA run.
**Requirements:** REQ-03, NFR-03
**Depends on:** Phase 2

**Plans:**
- [x] Plan 3.1: Flagsmith Management API client, credential encryption, SSRF protection, idempotent sync engine, webhook receiver, and full UI.

---

### Phase 4: Code Intelligence & Static AST Scanner
**Status:** ✅ Complete
**Objective:** Tree-sitter / AST static scanner detecting feature-flag usage in JS/TS and Python with confidence scoring and reference tracking.
**Requirements:** REQ-04
**Depends on:** Phase 3

---

### Phase 5: Dependency Graph & Blast-Radius Engine
**Status:** ✅ Complete
**Objective:** Multi-tier dependency graph connecting flags, components, and services with blast-radius calculation.
**Requirements:** REQ-05
**Depends on:** Phase 4

---

### Phase 6: Chaos Lab Sandbox
**Status:** ✅ Complete
**Objective:** Synthetic staging-only scenario records; remote traffic generation, flag mutation, and restoration verification are not implemented.
**Requirements:** REQ-06
**Depends on:** Phase 5

---

### Phase 7: Live Monitor & Telemetry Pipeline
**Status:** ✅ Implemented; latest runtime telemetry not present
**Objective:** Authenticated OTLP/HTTP histogram ingestion, Collector forwarding, persisted project/environment attribution, histogram-aware aggregation. Automated ingestion coverage passed; the latest QA Monitor had zero telemetry windows. Real production telemetry is not claimed.
**Requirements:** REQ-07
**Depends on:** Phase 6

---

### Phase 8: Deterministic Risk Engine & Safety Policies
**Status:** ✅ Complete
**Objective:** Mathematical deterministic scoring and configurable policy rules.
**Requirements:** REQ-08
**Depends on:** Phase 7

---

### Phase 9: Release Guardian & Verified Rollback
**Status:** 🟡 Partial — advisory risk/release checks work; provider rollback is deliberately disabled (HTTP 501).
**Objective:** Risk-based release recommendations and safe rollback. Remote rollback remains disabled until a supported environment-scoped provider write, explicit approval, audit, locking and read-after-write verification are implemented.
**Requirements:** REQ-09
**Depends on:** Phase 8

---

### Phase 10: Cleanup Studio & Hybrid AI Explanation
**Status:** 🟡 Partial — suggestions and local review previews exist; the application-owned cleanup-to-PR lifecycle is not live-verified.
**Objective:** Stale-flag evidence, reviewable patch generation and structured explanation. GitHub API/PR lifecycle requires separate authorization and remains unverified in current QA.
**Requirements:** REQ-10
**Depends on:** Phase 9

---

### Phase 11: End-to-End Polish & Full Platform Delivery
**Status:** 🟡 Partial — fresh Docker health, migrations, tests and browser workflows passed on 2026-11-28. Fresh Flagsmith authentication/sync, live CLI comparison, application PR flow, production readiness and public hosting remain unverified or out of scope.
**Objective:** Unified platform verification, accurate integration classifications, comprehensive tests, installation docs and production limitations.
**Requirements:** REQ-11
**Depends on:** Phase 10
