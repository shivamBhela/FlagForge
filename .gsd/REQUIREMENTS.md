---
milestone: v1.0
updated: 2026-11-24T18:27:00Z
---

# Requirements

## Overview
Requirements derived from `SPEC.md` and `FLAGFORGE_FULL_BUILD_PROMPT.md` for end-to-end traceability.

---

## Functional Requirements

| ID | Requirement | Source | Phase | Status |
|----|-------------|--------|-------|--------|
| REQ-01 | Monorepo scaffolding with FastAPI backend, Next.js frontend, Docker Compose, and health checks | SPEC Goal 1 | 1 | Complete ✅ |
| REQ-02 | Multi-tenant auth, organizations, projects, environments, and RBAC with Alembic migrations | SPEC Goal 1 | 2 | Complete ✅ |
| REQ-03 | Flagsmith API adapter (Cloud & self-hosted), credential encryption, project/environment/flag sync, and webhook signature verification | SPEC Goal 1 | 3 | Partial — live sync verified; native webhook delivery pending |
| REQ-04 | Repository connection and Tree-sitter AST static code scanner for JS/TS and Python | SPEC Goal 2 | 4 | Verified locally ✅ |
| REQ-05 | Dependency graph model, inference engine, React Flow visualizer, and impact analysis | SPEC Goal 3 | 5 | Verified locally ✅ |
| REQ-06 | OpenTelemetry telemetry ingestion, aggregation pipeline, and demo app emitting attributed telemetry | SPEC Goal 5 | 6 | Live QA path verified ✅ |
| REQ-07 | Chaos Lab staging simulation engine with state snapshotting, traffic generation, and verified compensation cleanup | SPEC Goal 4 | 7 | Partial — simulation only; no traffic or remote mutation |
| REQ-08 | Deterministic versioned risk engine with configurable weights, score components, and hard policy rules | SPEC Goal 6 | 8 | Automated and QA telemetry tested ✅ |
| REQ-09 | Release Guardian rollback coordinator with distributed locks, idempotency, read-after-write verification, and audit logs | SPEC Goal 7 | 9 | Partial — rollback disabled pending provider write verification |
| REQ-10 | Hybrid AI explanation service (advisory-only, no-AI fallback) and Cleanup Studio with patch preview | SPEC Goal 8 | 10 | Partial — local patch preview verified; GitHub PR not implemented |
| REQ-11 | Complete test suite (unit, integration, e2e), security audit, and deployment guides (`README_SELF_HOSTED.md`, `README_CLOUD.md`) | SPEC Criteria | 11 | Partial — local evidence documented; clean-clone/security audit incomplete |

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
