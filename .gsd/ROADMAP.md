---
milestone: v1.0
version: 1.0.0
updated: 2026-11-24T17:42:00Z
---

# Roadmap

> **Current Phase:** 1 - Monorepo Foundation & Dev Environment
> **Status:** planning

## Must-Haves (from SPEC)

- [ ] Real Flagsmith Management API adapter & sync
- [ ] Safe static code scanner (TypeScript/JavaScript, Python)
- [ ] Dependency graph with evidence types & blast-radius analysis
- [ ] OpenTelemetry telemetry collector & demo application
- [ ] Isolated Chaos Lab with guaranteed snapshot/restore
- [ ] Deterministic risk engine with versioned formulas
- [ ] Release Guardian with verified automated rollback & audit trails
- [ ] Explainable AI advisory layer with no-AI fallback
- [ ] Production-ready Docker Compose & complete deployment instructions

---

## Phases

### Phase 1: Monorepo Foundation & Dev Environment
**Status:** 🔄 In Progress
**Objective:** Establish monorepo structure, FastAPI backend, Next.js shell, Docker Compose setup, `.env.example`, and verified `/health` endpoints.
**Requirements:** REQ-01, NFR-01

### Phase 2: Auth, Tenancy, RBAC & Data Model
**Status:** ⬜ Not Started
**Objective:** Implement multi-tenant data architecture (PostgreSQL, SQLAlchemy 2 async, Alembic), organization-scoped models, user authentication, RBAC, and credential encryption.
**Requirements:** REQ-02, NFR-02, NFR-03
**Depends on:** Phase 1

### Phase 3: Flagsmith Integration & Synchronizer
**Status:** ⬜ Not Started
**Objective:** Build backend adapter for Flagsmith Management API (Cloud/self-hosted), test connection, sync projects/environments/flags, and verify webhooks safely.
**Requirements:** REQ-03, NFR-03
**Depends on:** Phase 2

### Phase 4: Code Intelligence & Static AST Scanner
**Status:** ⬜ Not Started
**Objective:** Tree-sitter / AST static scanner detecting feature-flag usage in JS/TS and Python with confidence scoring and reference tracking.
**Requirements:** REQ-04
**Depends on:** Phase 3

### Phase 5: Dependency Intelligence & Graph Visualization
**Status:** ⬜ Not Started
**Objective:** Graph inference engine (explicit, inferred, manual edges), blast radius calculation, and React Flow frontend map.
**Requirements:** REQ-05, NFR-06
**Depends on:** Phase 4

### Phase 6: Runtime Observability & OpenTelemetry Ingestion
**Status:** ⬜ Not Started
**Objective:** OpenTelemetry metrics/traces ingestion pipeline, time-bucket aggregation, and instrumented demo app emitting attributed telemetry.
**Requirements:** REQ-06
**Depends on:** Phase 5

### Phase 7: Chaos Lab & Staging Simulation
**Status:** ⬜ Not Started
**Objective:** Isolated staging simulation orchestrator with state snapshotting, traffic stimulation, metric assertions, and guaranteed rollback verification.
**Requirements:** REQ-07
**Depends on:** Phase 6

### Phase 8: Deterministic Risk Engine
**Status:** ⬜ Not Started
**Objective:** Implement transparent, versioned risk formulas and hard policy constraints with explainable score components.
**Requirements:** REQ-08, NFR-04
**Depends on:** Phase 7

### Phase 9: Release Guardian & Verified Rollback
**Status:** ⬜ Not Started
**Objective:** Release Guardian coordinator supporting monitor/notify/approval/automatic policies, distributed locking, idempotency, read-after-write verification, and audit logs.
**Requirements:** REQ-09, NFR-05
**Depends on:** Phase 8

### Phase 10: Hybrid AI Layer & Cleanup Studio
**Status:** ⬜ Not Started
**Objective:** Schema-constrained advisory AI incident summaries (no-AI fallback), and Cleanup Studio generating AST-based patch previews and PR drafts.
**Requirements:** REQ-10
**Depends on:** Phase 9

### Phase 11: System Validation, Documentation & Final Polishing
**Status:** ⬜ Not Started
**Objective:** End-to-end integration tests, verification of all acceptance criteria, and finalized `README_SELF_HOSTED.md` and `README_CLOUD.md`.
**Requirements:** REQ-11
**Depends on:** Phase 10

---

## Progress Summary

| Phase | Status | Deliverable |
|-------|--------|-------------|
| 1 | 🔄 In Progress | Monorepo scaffold, FastAPI backend, Next.js shell, Docker Compose, Health endpoints |
| 2 | ⬜ | Auth, Organizations, RBAC, Database models, Alembic migrations |
| 3 | ⬜ | Flagsmith integration adapter, live sync, credential encryption |
| 4 | ⬜ | Tree-sitter AST static code scanner for JS/TS/Python |
| 5 | ⬜ | Dependency engine, React Flow interactive map |
| 6 | ⬜ | OpenTelemetry ingestion, aggregation pipeline, demo app |
| 7 | ⬜ | Chaos Lab staging simulation with snapshot & compensation |
| 8 | ⬜ | Deterministic risk engine with versioned algorithms |
| 9 | ⬜ | Release Guardian with verified rollback and audit logs |
| 10 | ⬜ | Advisory AI summaries & Cleanup Studio patch generator |
| 11 | ⬜ | Full test suite verification & final documentation |
