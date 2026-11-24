---
milestone: v1.0
updated: 2026-11-24T17:42:00Z
---

# Requirements

## Overview
Requirements derived from `SPEC.md` and `FLAGFORGE_FULL_BUILD_PROMPT.md` for end-to-end traceability.

---

## Functional Requirements

| ID | Requirement | Source | Phase | Status |
|----|-------------|--------|-------|--------|
| REQ-01 | Monorepo scaffolding with FastAPI backend, Next.js frontend, Docker Compose, and health checks | SPEC Goal 1 | 1 | Pending |
| REQ-02 | Multi-tenant auth, organizations, projects, environments, and RBAC with Alembic migrations | SPEC Goal 1 | 2 | Pending |
| REQ-03 | Flagsmith API adapter (Cloud & self-hosted), credential encryption, project/environment/flag sync, and webhook signature verification | SPEC Goal 1 | 3 | Pending |
| REQ-04 | Repository connection and Tree-sitter AST static code scanner for JS/TS and Python | SPEC Goal 2 | 4 | Pending |
| REQ-05 | Dependency graph model, inference engine, React Flow visualizer, and impact analysis | SPEC Goal 3 | 5 | Pending |
| REQ-06 | OpenTelemetry telemetry ingestion, aggregation pipeline, and demo app emitting attributed telemetry | SPEC Goal 5 | 6 | Pending |
| REQ-07 | Chaos Lab staging simulation engine with state snapshotting, traffic generation, and verified compensation cleanup | SPEC Goal 4 | 7 | Pending |
| REQ-08 | Deterministic versioned risk engine with configurable weights, score components, and hard policy rules | SPEC Goal 6 | 8 | Pending |
| REQ-09 | Release Guardian rollback coordinator with distributed locks, idempotency, read-after-write verification, and audit logs | SPEC Goal 7 | 9 | Pending |
| REQ-10 | Hybrid AI explanation service (advisory-only, no-AI fallback) and Cleanup Studio with patch preview | SPEC Goal 8 | 10 | Pending |
| REQ-11 | Complete test suite (unit, integration, e2e), security audit, and deployment guides (`README_SELF_HOSTED.md`, `README_CLOUD.md`) | SPEC Criteria | 11 | Pending |

---

## Non-Functional Requirements

| ID | Requirement | Category | Phase | Status |
|----|-------------|----------|-------|--------|
| NFR-01 | API endpoints respond with structured envelopes and consistent error formatting | Architecture | 1 | Pending |
| NFR-02 | Tenant isolation enforced on all database queries via organization ownership | Security | 2 | Pending |
| NFR-03 | Zero plaintext storage of API tokens and integration credentials | Security | 2, 3 | Pending |
| NFR-04 | Deterministic risk calculations (same inputs always produce identical score and band) | Reliability | 8 | Pending |
| NFR-05 | Rollback operations are idempotent and fail-safe | Safety | 9 | Pending |
| NFR-06 | Dark theme modern UI with responsive layouts, empty states, and accessible contrast | UX | All | Pending |

---

## Traceability Matrix

| Requirement | Plans | Tests | Status |
|-------------|-------|-------|--------|
| REQ-01 | Phase 1 | test_health.py | Pending |
| REQ-02 | Phase 2 | test_auth.py, test_tenancy.py | Pending |
| REQ-03 | Phase 3 | test_flagsmith_adapter.py | Pending |
| REQ-04 | Phase 4 | test_code_scanner.py | Pending |
| REQ-05 | Phase 5 | test_dependency_engine.py | Pending |
| REQ-06 | Phase 6 | test_telemetry.py | Pending |
| REQ-07 | Phase 7 | test_chaos_lab.py | Pending |
| REQ-08 | Phase 8 | test_risk_engine.py | Pending |
| REQ-09 | Phase 9 | test_guardian_rollback.py | Pending |
| REQ-10 | Phase 10 | test_ai_explanation.py, test_cleanup.py | Pending |
| REQ-11 | Phase 11 | pytest, e2e smoke | Pending |
