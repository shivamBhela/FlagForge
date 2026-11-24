# SPEC.md — Project Specification

> **Status**: `FINALIZED`
>
> ⚠️ **Planning Lock**: No code may be written until this spec is marked `FINALIZED`.

## Vision
FlagForge is a production-grade, developer-friendly feature-release intelligence platform built around a real Flagsmith integration. It connects source-code intelligence, feature-flag management, dependency analysis, controlled release simulation, runtime observability, and policy-governed automated recovery into a unified safety and decision layer. Flagsmith serves as the system of record for feature flags, while FlagForge provides deterministic risk analysis, dependency graphing, and verified rollback orchestration around it.

## Goals
1. **Flagsmith Integration**: Connect to Flagsmith Cloud and self-hosted instances; sync projects, environments, flags, and states; execute read-after-write verified mutations; securely handle webhooks.
2. **Code Intelligence**: AST/Tree-sitter scanning for TypeScript/JavaScript and Python to locate feature-flag references with file, line, symbol, confidence, and evidence.
3. **Dependency Intelligence**: Construct an evidence-based dependency graph (explicit, inferred, manual) linking flags, code components, services, and APIs with React Flow visualization and blast-radius impact analysis.
4. **Chaos Lab**: Provide controlled, isolated test-scenario execution in staging environments with automated pre-run snapshots, traffic stimulation, metric assertions, and guaranteed rollback verification.
5. **Runtime Intelligence & OpenTelemetry**: Ingest OTel-compatible metrics and traces to track error rate, request volume, and latency percentiles with feature attribution.
6. **Deterministic Risk Engine**: Calculate repeatable, versioned, transparent risk scores combining weighted formula components with strict guardrail policies.
7. **Release Guardian & Verified Rollback**: Enforce policy modes (`monitor`, `notify`, `approval_required`, `automatic`) with distributed locking, idempotency keys, pre-flight checks, state verification, and audit logging.
8. **Hybrid AI & Cleanup Studio**: Offer advisory-only LLM explanations (with strict zero-mutation isolation and no-AI fallback) and interactive code cleanup patch generation.

## Non-Goals (Out of Scope)
- Reimplementing Flagsmith feature flag evaluation logic or replacing Flagsmith as the system of record.
- Autonomous AI-authorized mutations or AI-approved rollbacks.
- Running untrusted or arbitrary repository code directly in the core API process.
- Executing Chaos Lab simulations against production environments.
- Guaranteeing rollback of database migrations or persistent storage mutations.

## Constraints
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.x async, Alembic, Pydantic v2.
- Database: PostgreSQL with UUID primary keys and organization-level tenant isolation.
- Cache & Workers: Redis with Celery or async background task runners and distributed locks.
- Frontend: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, React Flow.
- Security: Integration secrets encrypted at rest; no Management API keys exposed to browser or logs; SSRF protections on custom URLs.
- Verification: Every mutating API request to Flagsmith must be followed by a read-after-write verification.

## Success Criteria
- [ ] Clean local execution via Docker Compose and native setup with health checks passing.
- [ ] Verified live connection and synchronization with Flagsmith API.
- [ ] Static scanner accurately discovers flag calls in Python and TypeScript test codebases.
- [ ] Dependency graph renders interactive nodes and edges with evidence types and confidence ratings.
- [ ] Controlled simulation executes in staging, stimulates metrics, and cleanly restores snapshot state.
- [ ] Deterministic risk engine produces identical scores for identical telemetry inputs.
- [ ] Release Guardian safely triggers and verifies rollback when policies breach, refusing when preconditions fail.
- [ ] Complete test suite passing with high coverage and reproducible documentation.

---

*Last updated: 2026-11-24*
