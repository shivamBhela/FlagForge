# FlagForge Project State

## Current Position

- **Status**: Official self-hosted Flagsmith and live FlagForge synchronization verified locally; broader platform readiness remains partial.
- **Assessment date**: 2026-11-26.
- **Docker**: 10 long-running services healthy; both migration jobs exited 0. Host ports 5433/6380 avoid existing listeners.
- **Database**: FlagForge Postgres is at Alembic revision `004_unify_dependency_node_enum`; Flagsmith uses a separate Postgres database and volume.
- **Backend**: 27 tests passed, including a regression assertion for the PostgreSQL graph enum.
- **Frontend**: `npx tsc --noEmit` and `npm run build` passed; production build generated 20 application routes.
- **Live Flagsmith**: Official `v2.295.2` image pinned by digest. The local connection discovered one project. A Staging-only OFF change was detected. Additional demo flags synchronized successfully.

## Verified implementation

- Docker Compose includes the seven FlagForge services, official self-hosted Flagsmith, separate Flagsmith PostgreSQL, task processor, and migration jobs.
- FlagForge API registered/authenticated a dedicated QA user and created an isolated organization/project/environment set.
- The Flagsmith Management API token is encrypted by FlagForge and does not appear in its connection response.
- Local Flagsmith state is authoritative; one state mutation was made only in the dedicated Staging environment. Development and Production remained ON.
- Setup, stop, health-check, architecture, integration, security, and local Flagsmith instructions are documented.
- Tests are isolated from `.env`, so developer-local secrets and service URLs do not affect assertions.
- Fixed Flags page response mapping, validation error rendering, and PostgreSQL dependency graph enum mismatch during QA.
- Headed Playwright swept 18 frontend routes; registration, organization/project creation, reload persistence, mobile width, synthetic staging simulation, cleanup preview, and search were exercised.

## Known limits

- Worker is a healthy placeholder and consumes no Redis jobs.
- OpenTelemetry Collector health is verified, but its OTLP data does not reach FlagForge's telemetry aggregate store.
- Chaos Lab is synthetic and does not mutate Flagsmith or run traffic.
- Release Guardian remote rollback and GitHub PR creation return HTTP 501.
- Native Flagsmith webhook delivery/signature compatibility has not been verified.
- Playwright route coverage and responsive/persisted-session checks passed. Live logout/re-login and live Flags page mapping were not repeated; the page response mapping was verified with a mocked API response in the automated browser check.
- The live graph defect was fixed through migration 004; Collector-to-FlagForge telemetry remains disconnected.
- Fresh-clone onboarding has not been repeated on a second machine; TLS, backups, and production hardening are absent.

## Latest QA snapshot

**Objective:** Deploy the official, pinned Flagsmith service beside FlagForge and demonstrate real local synchronization without overstating product capability.

**Changes:** Fixed Docker startup/config issues, added `email-validator`, corrected local Flagsmith host allowlisting, added local deployment/integration/security docs and helper scripts, and made two backend tests deterministic in the presence of `.env`.

**Verification:** `27 passed`; TypeScript check passed; Next production build passed; Compose config passed; health script reported 10 healthy long-running services and 2 successful migration jobs; migration `004_unify_dependency_node_enum` applied; live graph returned 6 nodes and 5 edges after fix; real connection/sync/state-change/replay passed; headed Playwright route sweep passed.

**Next work:** Replace the worker placeholder, wire Collector telemetry into persisted metrics, validate native provider webhooks, and implement GitHub/rollback integrations only with documented safe provider behavior.
