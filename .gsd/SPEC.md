# SPEC.md — FlagForge Specification

> **Status**: `FINALIZED`
>
> ⚠️ **Planning Lock**: SPEC is FINALIZED. Milestone 1 planning and execution authorized.

## Vision
FlagForge is an open-source, developer-first feature flagging and experimentation platform built for speed, resilience, and multi-environment observability. It empowers engineering teams to decouple deployments from releases, perform targeted canary rollouts, and monitor feature impact via distributed telemetry.

## Goals
1. **Developer Experience** — Provide a zero-friction, one-command local setup environment orchestration with comprehensive Docker Compose infrastructure.
2. **High-Performance Flag Evaluation** — Sub-millisecond flag evaluation backed by in-memory Redis caching and PostgreSQL persistence.
3. **End-to-End Observability** — Native OpenTelemetry instrumentation exporting traces, metrics, and logs across all services.
4. **Production Parity** — Monorepo architecture containing admin web dashboard, core API, background worker, sample demo app, and shared SDKs.

## Non-Goals (Out of Scope for Milestone 1)
- Multi-region database replication.
- Production Kubernetes Helm charts (deferred to later milestone).
- Full enterprise SSO / SAML integration (local development auth only in Milestone 1).

## Architecture & Services
| Service | Technology | Role |
|---------|------------|------|
| `web` | Next.js / TypeScript | Feature management dashboard & UI |
| `api` | Node.js / Express / TypeScript | Core REST/gRPC API for flag evaluations and admin |
| `worker` | Node.js / TypeScript | Async event processing, webhook delivery, analytics |
| `postgres` | PostgreSQL 16 Alpine | Primary relational storage for flags, rules, audit logs |
| `redis` | Redis 7 Alpine | Fast flag cache & message queue |
| `otel-collector` | OpenTelemetry Collector Contrib | Aggregates and exports distributed traces & metrics |
| `demo-app` | Node.js / TypeScript | Client application demonstrating SDK integration & telemetry |

## Success Criteria for Milestone 1
- [x] Monorepo scaffolded with workspace configuration (pnpm / Turborepo).
- [x] Docker Compose orchestrates all 7 services (`web`, `api`, `worker`, `postgres`, `redis`, `otel-collector`, `demo-app`).
- [x] Core API exposes deep health-check endpoint (`/healthz`) confirming PostgreSQL and Redis connectivity.
- [x] Executable one-command setup script boots the stack and confirms operational health.

---
*Last updated: 2026-11-24*
