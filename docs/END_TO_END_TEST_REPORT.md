# End-to-End Test Report

**Run date:** 2026-11-28 (latest rerun update)
**Targets:** Current headed browser run against the Windows Docker Desktop Compose deployment at `http://localhost:3000`, with the API backed by PostgreSQL.
**Data scope:** The E2E run created a disposable FlagForge account, organization, project, environment and synthetic fixtures in the existing local QA database. It did not alter any Flagsmith provider data. Existing named Docker volumes were preserved.

**Branch scope:** This evidence was recorded on `completion/final-readiness` at commit `3d64c6d`. The repository-hygiene branch is based on `main`, which differs in backend tests and frontend code. These results describe that tested revision and do not certify the current branch. Fresh hygiene-branch checks are recorded in the repository audit and root README.

**Fresh run note (2026-11-28):** After a temporary Docker Desktop/WSL engine stall, Docker Desktop was restarted without deleting volumes. The same stack recovered. Fresh reruns: backend pytest 46 passed (21.84s, one upstream warning); CLI pytest 12 passed (0.19s); frontend lint, TypeScript and production build passed (20 routes); `npm audit --audit-level=low` found 0 vulnerabilities; headed Playwright 1 passed (19.8s test, 25.6s total); Full-profile health passed with 10/10 long-running services healthy, both migration jobs exit 0, HTTP checks passing and Alembic current/head `009_encrypt_webhook_secrets`. The fresh browser workflow used synthetic local fixtures; no Flagsmith instance was connected or synchronized. See ignored local evidence at `../artifacts/evidence/` and the evidence index at `../artifacts/evidence/EVIDENCE_INDEX.md`.

## Commands and results

| Check | Status | Evidence |
| --- | --- | --- |
| `docker compose config --quiet` | **Passed** | Default configuration and explicit `COMPOSE_PROJECT_NAME=flagforge-clean-qa` both rendered successfully. |
| Compose profile service matrix | **Passed** | Default/Core, Dashboard, Observability and Full service lists rendered; Core omits web, Collector and demo app. Full profile runtime is healthy. |
| `docker compose up --build -d` | **Passed** | Default stack recreated with generated names and scoped network; named volumes were retained. |
| `scripts/health-check.ps1` | **Passed** | All 10 long-running services healthy; both one-shot migration containers exited 0; HTTP checks passed for API, web, demo app, Flagsmith liveness and Collector health. |
| Alembic current | **Passed** | `009_encrypt_webhook_secrets (head)`. |
| Backend pytest in project container | **Passed (earlier run)** | 35 passed, one Starlette/httpx deprecation warning. |
| Backend pytest in isolated host venv | **Passed (latest)** | `backend\.venv\Scripts\python.exe -m pytest -q`: 46 passed, one upstream Starlette/httpx deprecation warning; includes eight risk-band boundary cases and three login-rate-limit tests. |
| `npx tsc --noEmit` | **Passed** | Exit code 0. |
| `npm run build` | **Passed** | Next.js 16.4.6 production build generated all 20 app routes. |
| `npm audit` / `npm audit --omit=dev` | **Passed** | Both report zero known vulnerabilities. |
| Headed Playwright Chromium | **Passed** | 1 end-to-end workflow passed against the rebuilt production container and again against a fresh isolated checkout. |
| Clean-checkout installation | **Passed** | Committed `acd08d4` cloned separately, documented `setup.ps1` built and started the stack with a distinct Compose name/volumes; all service and HTTP health checks passed. |
| `npm run lint` | **Passed** | All 34 previously recorded findings were fixed; no rule suppression or configuration weakening. |
| Latest headed Playwright run | **Passed (fresh Compose run, 2026-11-28)** | 1 test passed in 19.8 seconds (25.6 seconds total). Invalid-form validation, registration/login, org/project/environment CRUD, 18 route experiences, synthetic Chaos, flag/scanner search, dependency-map refresh, Staging monitoring refresh, Guardian safety output, incident empty states, cleanup draft preview, integration form validation, 390px mobile width, logout/login and persistence passed. No page errors, HTTP 5xx or unexpected failed requests; navigation cancellations are separately recorded. Raw output and 19 screenshots are in ignored `artifacts/evidence/playwright/`. |
| Latest Docker status check | **Passed** | Ten long-running services healthy; both one-shot migrations exited 0; Alembic `009_encrypt_webhook_secrets (head)`; Full profile health and HTTP checks passed. |
| Docker memory snapshot | **Passed (point-in-time)** | Latest `docker stats --no-stream` measured approximately 0.98 GiB across ten running services against the 3.67 GiB Docker VM limit; this was not a peak/load/soak measurement. |
| Companion CLI unit tests | **Passed (latest; diff responses mocked)** | `python -m unittest discover -s cli/tests -v`: 12 passed, including environment diff classification, duplicate/same-environment rejection, no-input handling and provider error redaction. |
| Latest frontend lint/type/build | **Passed** | `npm run lint`, `npx tsc --noEmit`, and `npm run build` exited 0; build generated 20 routes (19 static, one dynamic project-detail route). Full and production-only `npm audit` each reported zero vulnerabilities. |
| GitHub Actions CI | **Passed (hosted)** | Run 46136196032 completed successfully for published commit `ff845152950de8710aded61981b5d4fe2349808f`. |

## Browser workflow

- Verified invalid email validation, then registered a disposable account and created an organization, project and custom environment; verified organization persistence after reload.
- Seeded synthetic demo fixtures in the disposable QA organization and confirmed the response identified them as local synthetic data.
- Opened all 18 existing routes, including the created project detail, and waited beyond loading states. Interacted with scanner search, flag search/filter, synthetic Chaos Lab, dependency-map refresh, Staging monitoring refresh, Guardian advisory output, incident empty states and the cleanup draft preview. Confirmed Integrations shows the disconnected state and the Settings route shows the QA owner's membership.
- Confirmed Chaos Lab stated that it performed no remote flag mutation. The Production lock remained active.
- Checked a 390px mobile viewport for horizontal overflow.
- Logged out and back in; verified organization persistence. Uncaught browser page errors and HTTP 5xx responses: none.
- The first upgraded-app E2E attempt exposed two harness ordering issues (public auth-route sweep and home-page hydration). The test was corrected and the entire headed suite rerun successfully.
- A final regression assertion verifies that a Critical risk with sufficient histogram data still recommends manual approval while rollback is unavailable. The isolated test passed, then the full backend suite was rerun.
- The route sweep verifies all route content beyond loading; controls listed above were separately exercised. Integrations form validation was tested with an empty token and returned its required-fields message without sending a provider request. Read-only provider-dependent paths were not represented as a live provider test.

Screenshots, traces and test output are in the ignored `frontend/test-results/` and `frontend/playwright-report/` directories. These files contain synthetic QA data only and are not committed.

The earlier Docker-backed registration request remained pending during the Flagsmith/Gunicorn memory failure. The current Compose-backed browser pass verifies registration no longer hangs on the running stack. No unexpected failed network requests occurred; route-change `ERR_ABORTED` cancellations were treated as expected. It does not verify a new live provider session; the single fresh login attempt to the local Flagsmith UI using the supplied account was rejected. No repeated attempts were made.

The fresh isolated checkout at `C:\Users\unbel\Downloads\FlagForge_CleanInstall_QA` also passed the headed Playwright run historically (1 passed, 32.6 seconds). The default project's named volumes were preserved; the fresh checkout created a separate set of volumes. Both installs ran on the same Windows/Docker Desktop host. In this latest run, the same existing stack recovered from a temporary Docker Desktop/WSL stall after an engine restart; no volumes or database contents were reset.

The read-only CLI environment diff has mocked response coverage only; no source/target environment keys were supplied for a live comparison. Current QA did not reconnect to Flagsmith; the earlier local Management API and Staging webhook/sync results below are historical live evidence. The isolated restore drill passed for both FlagForge and Flagsmith PostgreSQL dumps in temporary tmpfs-backed databases; the existing project volumes were not mounted or changed. A first harness attempt failed before the corrected rerun passed. Raw logs are in `../artifacts/evidence/docker/restore_drill_20261128_144218.log`.

## Real and mocked integrations

- **Flagsmith real local API:** official 2.295.2 instance, pinned by digest. Existing evidence covers project/environment/flag discovery and synchronization, including Staging-only state change detection; Development and Production remained unchanged.
- **Flagsmith live webhook:** provider-signed test callback plus two actual Staging flag updates (enable and restore) were delivered to the private Compose alias, processed, and reconciled. Database evidence shows processed webhook events and completed webhook-triggered sync history. The test flag read back disabled; the temporary provider webhook was removed and the local webhook signing secret cleared. Provider retry behavior and outage recovery were not tested.
- **GitHub:** the feature branch is published and draft PR [#1](https://github.com/shivamBhela/FlagForge/pull/1) is open against `main`, unmerged. FlagForge's own cleanup-to-PR workflow remains mocked/unverified.
- **Redis worker:** durable Flagsmith sync/repository scan processing and restart recovery were verified previously. `scripts/test-worker-recovery.ps1` additionally verified queued-job completion after restart, graceful SIGTERM, heartbeat removal and healthy restart; no new job types were introduced.
- **OpenTelemetry:** prior end-to-end QA sent demo-app OTLP traffic through the Collector into authenticated, tenant-attributed storage and verified Monitor/Risk outputs. Demo telemetry is not customer traffic.
- **Chaos Lab:** synthetic demonstration only; no load and no provider mutation.
- **Rollback:** disabled with HTTP 501; no provider mutation is represented as successful.

## Remaining limitations

- A second physical machine was not available; clean install evidence covers a separate checkout with isolated volumes on this host only.
- Live GitHub authentication/PR lifecycle and race-safe provider rollback are unverified.
- Provider webhook retries, TLS/public ingress, production restore procedures beyond the isolated drill, HA/load and independent penetration testing are unverified.
- Public hosting is paused by user direction to keep hosting local at ₹0. Render showed no card, zero usage and no pending charges, but included bandwidth/pipeline overages can be billed and no zero-spend cap was verified; no Render resources were created.
- Redis-backed login rate limiting passed unit tests and a live local check against the rebuilt Docker API/Redis (eight 401 responses followed by 429 with `Retry-After`). TypeScript, full lint and production build pass.
