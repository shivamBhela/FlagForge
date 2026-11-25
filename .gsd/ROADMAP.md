---
milestone: "FlagForge Application Core"
version: "0.2.0"
updated: "2026-11-24T18:27:00Z"
---

# FlagForge Roadmap

> **Current Phase:** 2 - Application Core
> **Status:** complete

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
**Status:** ✅ Complete
**Objective:** Backend adapter for Flagsmith Management API (Cloud/self-hosted), connection tests, project/environment/flag synchronization, read-after-write verification, and secure webhook handler.
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
**Status:** ✅ Complete
**Objective:** OpenTelemetry ingestion and rolling window metrics aggregation.
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
**Status:** ✅ Complete
**Objective:** Pre-conditions check, distributed locking, atomic rollback execution, and read-after-write verification.
**Requirements:** REQ-09
**Depends on:** Phase 8

---

### Phase 10: Cleanup Studio & Hybrid AI Explanation
**Status:** ✅ Complete
**Objective:** Stale flag elimination, unified diff patch generator, GitHub PR opening, and structured explanation with NO-AI fallback.
**Requirements:** REQ-10
**Depends on:** Phase 9

---

### Phase 11: End-to-End Polish & Full Platform Delivery
**Status:** ✅ Complete
**Objective:** Unified platform verification, seed data, comprehensive tests, and production documentation.
**Requirements:** REQ-11
**Depends on:** Phase 10
**Objective:** Tree-sitter / AST static scanner detecting feature-flag usage in JS/TS and Python with confidence scoring and reference tracking.
**Requirements:** REQ-04
**Depends on:** Phase 3
