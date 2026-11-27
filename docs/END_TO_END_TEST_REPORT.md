# End-to-End Test Report

**Run date:** 2026-11-28 (latest rerun update)
**Targets:** Current headed browser run against the Windows Docker Desktop Compose deployment at `http://localhost:3000`, with the API backed by PostgreSQL.
**Data scope:** The E2E run created a disposable FlagForge account, organization, project, environment and synthetic fixtures in the existing local QA database. It did not alter any Flagsmith provider data. Existing named Docker volumes were preserved.

## Commands and results

| Check | Status | Evidence |
| --- | --- | --- |
| `docker compose config --quiet` | **Passed** | Default configuration and explicit `COMPOSE_PROJECT_NAME=flagforge-clean-qa` both rendered successfully. |
| Compose profile service matrix | **Passed** | Default/Core, Dashboard, Observability and Full service lists rendered; Core omits web, Collector and demo app. Full profile runtime is healthy. |
| `docker compose up --build -d` | **Passed** | Default stack recreated with generated names and scoped network; named volumes were retained. |
| `scripts/health-check.ps1` | **Passed** | All 10 long-running services healthy; both one-shot migration containers exited 0; HTTP checks passed for API, web, demo app, Flagsmith liveness and Collector health. |
| Alembic current | **Passed** | `009_encrypt_webhook_secrets (head)`. |
| Backend pytest in project container | **Passed** | 35 passed, one Starlette/httpx deprecation warning. |
| Backend pytest in isolated host venv | **Passed (current)** | `backend\.venv\Scripts\python.exe -m pytest -q`: 35 passed, one upstream Starlette/httpx deprecation warning. |
| `npx tsc --noEmit` | **Passed** | Exit code 0. |
| `npm run build` | **Passed** | Next.js 16.4.6 production build generated all 20 app routes. |
| `npm audit` / `npm audit --omit=dev` | **Passed** | Both report zero known vulnerabilities. |
| Headed Playwright Chromium | **Passed** | 1 end-to-end workflow passed against the rebuilt production container and again against a fresh isolated checkout. |
| Clean-checkout installation | **Passed** | Committed `acd08d4` cloned separately, documented `setup.ps1` built and started the stack with a distinct Compose name/volumes; all service and HTTP health checks passed. |
| `npm run lint` | **Passed** | All 34 previously recorded findings were fixed; no rule suppression or configuration weakening. |
| Latest headed Playwright run | **Passed (current Compose run)** | 1 test passed in 14.8 seconds against Compose web/API/PostgreSQL. Invalid-form validation, registration/login, org/project/environment CRUD, 18 route experiences, synthetic Chaos, flag/scanner search, dependency-map refresh, Staging monitoring refresh, Guardian safety output, incident empty states, cleanup draft preview, integration form validation, 390px mobile width, logout/login and persistence passed. No page errors, HTTP 5xx or unexpected failed requests; navigation cancellations are separately recorded. |
| Latest Docker status check | **Passed** | Ten long-running services healthy; both one-shot migrations exited 0; Alembic `009_encrypt_webhook_secrets (head)`; Full profile health and HTTP checks passed. |
| Companion CLI unit tests | **Passed** | `python -m unittest discover -s cli/tests -v`: 6 passed. |
| Latest frontend lint/type/build | **Passed** | `npm run lint`, `npx tsc --noEmit`, and `npm run build` exited 0; build generated 20 routes. |

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

The fresh isolated checkout at `C:\Users\unbel\Downloads\FlagForge_CleanInstall_QA` also passed the headed Playwright run (1 passed, 32.6 seconds). The default project's named volumes were preserved; the fresh checkout created a separate set of volumes. Both installs ran on the same Windows/Docker Desktop host.

## Real and mocked integrations

- **Flagsmith real local API:** official 2.295.2 instance, pinned by digest. Existing evidence covers project/environment/flag discovery and synchronization, including Staging-only state change detection; Development and Production remained unchanged.
- **Flagsmith live webhook:** provider-signed test callback plus two actual Staging flag updates (enable and restore) were delivered to the private Compose alias, processed, and reconciled. Database evidence shows processed webhook events and completed webhook-triggered sync history. The test flag read back disabled; the temporary provider webhook was removed and the local webhook signing secret cleared. Provider retry behavior and outage recovery were not tested.
- **GitHub:** the feature branch is published at `72ebc9912f8cceda204e2cfb599a793b5ad6dbc4`. Draft PR [#1](https://github.com/shivamBhela/FlagForge/pull/1) is open against `main`, unmerged. FlagForge's own cleanup-to-PR workflow remains mocked/unverified.
- **Redis worker:** durable Flagsmith sync/repository scan processing and restart recovery were verified previously. `scripts/test-worker-recovery.ps1` additionally verified queued-job completion after restart, graceful SIGTERM, heartbeat removal and healthy restart; no new job types were introduced.
- **OpenTelemetry:** prior end-to-end QA sent demo-app OTLP traffic through the Collector into authenticated, tenant-attributed storage and verified Monitor/Risk outputs. Demo telemetry is not customer traffic.
- **Chaos Lab:** synthetic demonstration only; no load and no provider mutation.
- **Rollback:** disabled with HTTP 501; no provider mutation is represented as successful.

## Remaining limitations

- A second physical machine was not available; clean install evidence covers a separate checkout with isolated volumes on this host only.
- Live GitHub authentication/PR lifecycle and race-safe provider rollback are unverified.
- Provider webhook retries, TLS/public ingress, backup restore, HA/load and independent penetration testing are unverified.
- Public hosting is not deployed; no hosting provider/account connection was available, and no charges were incurred.
- Request rate limiting is not implemented. TypeScript, full lint and production build pass.
