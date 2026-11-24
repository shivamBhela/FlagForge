---
milestone: "FlagForge Infrastructure Foundation"
version: "0.1.0"
updated: "2026-11-24T12:00:00Z"
---

# FlagForge Roadmap

> **Current Phase:** 1 - Monorepo Scaffolding & Multi-Service Infrastructure
> **Status:** planning

## Must-Haves (from SPEC)

- [ ] Monorepo workspace scaffolded with shared tooling and service boundaries
- [ ] Docker Compose orchestrating all 7 services (`web`, `api`, `worker`, `postgres`, `redis`, `otel-collector`, `demo-app`)
- [ ] Deep health-check endpoint (`/healthz`) on API reporting database and cache status
- [ ] Automated one-command setup script for developer onboarding

---

## Phases

### Phase 1: Monorepo Scaffolding & Multi-Service Infrastructure
**Status:** ✅ Complete
**Objective:** Scaffold the monorepo architecture, configure Docker Compose with all 7 services, implement deep health-check endpoints, and provide a one-command setup script.
**Requirements:** REQ-INFRA-01, REQ-INFRA-02, REQ-INFRA-03, REQ-INFRA-04

**Plans:**
- [x] Plan 1.1: Monorepo Scaffolding, Docker Compose (7 Services), Health-Check, and Setup Script

---

### Phase 2: Core Flag Engine & SDK
**Status:** 🔄 In Progress
**Objective:** Database schema migrations, flag evaluation engine, Redis caching layer, and client SDK.
**Depends on:** Phase 1

---

### Phase 3: Dashboard Web UI & Flag Management
**Status:** ⬜ Not Started
**Objective:** Web dashboard for feature flag creation, rollout rules, and user targeting.
**Depends on:** Phase 2

---

### Phase 4: Observability, Analytics & Worker
**Status:** ⬜ Not Started
**Objective:** OpenTelemetry distributed tracing pipeline, worker evaluation streaming, and demo-app telemetry integration.
**Depends on:** Phase 3

---

## Progress Summary

| Phase | Status | Plans | Complete |
|-------|--------|-------|----------|
| 1 | 🔄 | 0/1 | 0% |
| 2 | ⬜ | 0/2 | 0% |
| 3 | ⬜ | 0/2 | 0% |
| 4 | ⬜ | 0/2 | 0% |
