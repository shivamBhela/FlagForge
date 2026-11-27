# FlagForge Project State

## Current position

- **Status:** Earlier verified flows remain documented, but the current Docker stack is blocked and the latest registration browser rerun failed. This is not a production-readiness claim.
- **Assessment date:** 2026-11-28.
- **Docker:** Prior check showed all 10 long-running services healthy and both migration jobs exited 0. Current Docker Desktop reports 3.50/3.58 GB VM memory; Flagsmith restart stalled at 0%, then Docker restart failed with `HCS_E_CONNECTION_TIMEOUT`. Terminating only the Docker-managed WSL distro returned successfully, but Docker still cannot start. The Ubuntu WSL distro and named volumes were not touched. Windows restart/elevated WSL recovery is pending approval.
- **Database:** Alembic head is `009_encrypt_webhook_secrets`. Flagsmith uses its separate PostgreSQL volume.
- **Backend:** `docker compose run --rm --no-deps --build api python -m pytest tests/ -v` — **35 passed**, one Starlette/httpx deprecation warning.
- **Frontend:** Next.js 16.4.6, React 19.3.1. Full ESLint (zero findings), TypeScript and production build pass. `npm audit` and `npm audit --omit=dev` report zero vulnerabilities.
- **Browser:** Earlier headed Chromium E2E passed the registration/login/logout, org/project/environment, 18-route, synthetic Staging, search/filter, responsive, persistence, and console/network checks. The latest rerun failed: registration POST remained pending with `Creating account...`; retry after Docker recovery is required.
- **Clean installation:** Fresh clone of committed revision `acd08d4` passed documented `setup.ps1`, independent Compose-scoped volumes, both migration jobs, health script and headed Playwright workflow (1 passed). Same Windows host; no second-host claim.
- **Provider webhook:** A signed provider test callback and actual Staging test-flag enable/restore events were delivered and processed. FlagForge recorded event/sync history; the flag was restored disabled and temporary webhook/secret removed.

## Verified implementation

- Official Flagsmith 2.295.2 is pinned by digest. Real Management API discovery/sync and Staging-only state changes were previously verified; Development and Production were not modified.
- Webhook callback uses the private Compose alias `api.flagforge.local` in Flagsmith's exact `SSRF_ALLOWED_HOSTS` allowlist. The provider SSRF validator remains active for all other targets.
- GitHub App/PAT integration supports authorized repository discovery, selection and reviewed, idempotent single-file PR creation without auto-merge. Mock/tenant tests pass; no GitHub credentials or authorized external repository are configured.
- Redis Streams worker handles Flagsmith sync and repository scan jobs with persisted status, retry/backoff and restart recovery.
- New worker recovery script verified queued-job completion after restart, graceful SIGTERM, heartbeat removal and healthy restart.
- Official Flagsmith CLI v2.0.0 help and live local read-only `evaluate` returned successfully; no credential values were printed. Companion CLI tests: 6 passed. Its unsupported diff, telemetry, mutation, and PR operations are documented as partial/not implemented.
- Latest frontend lint, TypeScript, Next production build (20 routes), CLI unit suite (6 tests), and production npm audit (0 vulnerabilities) passed. A host pytest attempt was blocked because the host Python environment lacks the `redis` package; the earlier container suite had 35 passed.
- Release Guardian Critical assessments require manual approval and mark rollback unavailable; rollback remains HTTP 501.
- Demo-app OTLP traffic persists tenant-attributed request/error histograms through Collector and FlagForge ingestion; Runtime Monitor and Risk Engine were verified.
- Cleanup patch proposal requires a real repository file diff and explicit administrator approval.
- Compose project names and generated container/network names support an isolated second checkout. Setup port collision detection reads configured `.env` ports.

## Remaining limitations and follow-up

- Live GitHub API/PR lifecycle is blocked: `origin` now points to the public repository, but `git ls-remote` is empty and Git Credential Manager supplied no credential during a noninteractive push check. Browser sign-in is required before push.
- Remote rollback remains HTTP 501 and makes no provider change because race-safe conditional writes are not established.
- Chaos Lab is synthetic; it sends no load and performs no remote mutation.
- Worker scope remains Flagsmith sync and repository scans; other lightweight operations remain synchronous.
- Provider retry/outage semantics, TLS, public ingress, backup restoration, HA and independent penetration testing remain unverified.
- Request rate limiting is not implemented. Public TLS/ingress, backup restore, HA and independent penetration testing remain unverified.
- Current Docker recovery and successful registration browser rerun are open blockers; see root `FINAL_COMPETITION_READINESS_REPORT.md` and `docs/END_TO_END_TEST_REPORT.md`.
