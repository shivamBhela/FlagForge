# FlagForge Project State

## Current position

- **Status:** Local FlagForge and official self-hosted Flagsmith are operational for the verified flows. This is not a production-readiness claim.
- **Assessment date:** 2026-11-26.
- **Docker:** All 10 long-running services healthy. FlagForge and Flagsmith migrations exited 0. Existing named volumes were retained.
- **Database:** Alembic head is `009_encrypt_webhook_secrets`. Flagsmith uses its separate PostgreSQL volume.
- **Backend:** `docker compose run --rm --no-deps --build api python -m pytest tests/ -v` — **35 passed**, one Starlette/httpx deprecation warning.
- **Frontend:** Next.js 16.4.6, React 19.3.1. TypeScript and production build pass. `npm audit` and `npm audit --omit=dev` report zero vulnerabilities.
- **Browser:** Headed Chromium E2E passed, exercising registration/login/logout, organization/project/environment creation, all 18 routes, synthetic Staging workflow, search/filter, responsive width, persistence and no console/5xx errors.
- **Clean installation:** Fresh clone of committed revision `acd08d4` passed documented `setup.ps1`, independent Compose-scoped volumes, both migration jobs, health script and headed Playwright workflow (1 passed). Same Windows host; no second-host claim.
- **Provider webhook:** A signed provider test callback and actual Staging test-flag enable/restore events were delivered and processed. FlagForge recorded event/sync history; the flag was restored disabled and temporary webhook/secret removed.

## Verified implementation

- Official Flagsmith 2.295.2 is pinned by digest. Real Management API discovery/sync and Staging-only state changes were previously verified; Development and Production were not modified.
- Webhook callback uses the private Compose alias `api.flagforge.local` in Flagsmith's exact `SSRF_ALLOWED_HOSTS` allowlist. The provider SSRF validator remains active for all other targets.
- GitHub App/PAT integration supports authorized repository discovery, selection and reviewed, idempotent single-file PR creation without auto-merge. Mock/tenant tests pass; no GitHub credentials or authorized external repository are configured.
- Redis Streams worker handles Flagsmith sync and repository scan jobs with persisted status, retry/backoff and restart recovery.
- Demo-app OTLP traffic persists tenant-attributed request/error histograms through Collector and FlagForge ingestion; Runtime Monitor and Risk Engine were verified.
- Cleanup patch proposal requires a real repository file diff and explicit administrator approval.
- Compose project names and generated container/network names support an isolated second checkout. Setup port collision detection reads configured `.env` ports.

## Remaining limitations and follow-up

- Live GitHub API/PR lifecycle is blocked by missing credentials.
- Remote rollback remains HTTP 501 and makes no provider change because race-safe conditional writes are not established.
- Chaos Lab is synthetic; it sends no load and performs no remote mutation.
- Worker scope remains Flagsmith sync and repository scans; other lightweight operations remain synchronous.
- Provider retry/outage semantics, TLS, public ingress, backup restoration, HA and independent penetration testing remain unverified.
- Supplemental ESLint run reports 34 existing source findings (15 hook state-in-effect, 14 dependency-array, 2 internal navigation, 2 unescaped text, 1 immutability). TypeScript/build/E2E pass; lint debt is not hidden or presented as a passing check.
