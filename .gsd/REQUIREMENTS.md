---
milestone: v1.0
updated: 2026-11-24T18:27:00Z
---

# Requirements

## Overview
Requirements derived from `.gsd/SPEC.md` and the archived original build prompt (`docs/archive/ORIGINAL_BUILD_PROMPT.md`) for end-to-end traceability.

---

## Functional Requirements

| ID | Requirement | Source | Phase | Status |
|----|-------------|--------|-------|--------|
| REQ-01 | Monorepo scaffolding with FastAPI backend, Next.js frontend, Docker Compose, and health checks | SPEC Goal 1 | 1 | Complete ✅ |
| REQ-02 | Multi-tenant auth, organizations, projects, environments, and RBAC with Alembic migrations | SPEC Goal 1 | 2 | Complete ✅ |
| REQ-03 | Flagsmith API adapter (Cloud & self-hosted), credential encryption, project/environment/flag sync, and webhook signature verification | SPEC Goal 1 | 3 | Partial — isolated Staging sync and signed webhook passed historically; no connection was active in the latest Nov 28 QA |
| REQ-04 | Repository connection and Tree-sitter AST static code scanner for JS/TS and Python | SPEC Goal 2 | 4 | Verified locally ✅ |
| REQ-05 | Dependency graph model, inference engine, React Flow visualizer, and impact analysis | SPEC Goal 3 | 5 | Verified locally ✅ |
| REQ-06 | OpenTelemetry telemetry ingestion, aggregation pipeline, and demo app emitting attributed telemetry | SPEC Goal 5 | 6 | Automated ingestion path passed; latest Monitor had zero telemetry windows; no customer telemetry claimed |
| REQ-07 | Chaos Lab staging simulation engine with state snapshotting, traffic generation, and verified compensation cleanup | SPEC Goal 4 | 7 | Partial — synthetic Staging simulation only; no provider mutation or load generation |
| REQ-08 | Deterministic versioned risk engine with configurable weights, score components, and hard policy rules | SPEC Goal 6 | 8 | Automated and QA telemetry tested ✅ |
| REQ-09 | Release Guardian rollback coordinator with distributed locks, idempotency, read-after-write verification, and audit logs | SPEC Goal 7 | 9 | Partial — rollback disabled pending provider write verification |
| REQ-10 | Hybrid AI explanation service (advisory-only, no-AI fallback) and Cleanup Studio with patch preview | SPEC Goal 8 | 10 | Partial — local suggestions/previews exercised; app-owned GitHub PR lifecycle not verified |
| REQ-11 | Complete test suite (unit, integration, e2e), security audit, and self-hosted deployment guide (`docs/SELF_HOSTED_QUICKSTART.md`) | SPEC Criteria | 11 | Partial — local QA evidence documented; clean-clone/security audit incomplete; cloud draft is archived and unimplemented |

---

## Non-Functional Requirements

| ID | Requirement | Category | Phase | Status |
|----|-------------|----------|-------|--------|
| NFR-01 | API endpoints respond with structured envelopes and consistent error formatting | Architecture | 1 | Complete ✅ |
| NFR-02 | Tenant isolation enforced on all database queries via organization ownership | Security | 2 | Complete ✅ |
| NFR-03 | Zero plaintext storage of API tokens and integration credentials | Security | 2, 3 | Complete ✅ |
| NFR-04 | Deterministic risk calculations (same inputs always produce identical score and band) | Reliability | 8 | Automated tested ✅ |
| NFR-05 | Rollback operations are idempotent and fail-safe | Safety | 9 | Remote action disabled pending verification |
| NFR-06 | Dark theme modern UI with responsive layouts, empty states, and accessible contrast | UX | All | Complete ✅ |

---

## Traceability Matrix

| Requirement | Plans | Tests | Status |
|-------------|-------|-------|--------|
| REQ-01 | Phase 1 | test_health.py | Verified ✅ |
| REQ-02 | Phase 2 | test_auth.py, test_tenancy.py, test_projects.py, test_db_schema.py | Verified ✅ |
| REQ-03 | Phase 3 | test_flagsmith_adapter.py | Pending |
