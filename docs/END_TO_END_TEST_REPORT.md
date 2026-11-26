# End-to-End Test Report

**Run date:** 2026-11-26
**Target:** Local Windows Docker Desktop deployment; FlagForge at `http://localhost:3000`, Flagsmith at `http://localhost:8081`
**Data scope:** Dedicated local FlagForge QA accounts/projects and the existing local Flagsmith QA Staging project. Existing named volumes were preserved.

## Commands and results

| Check | Status | Evidence |
| --- | --- | --- |
| `docker compose config --quiet` | **Passed** | Default configuration and explicit `COMPOSE_PROJECT_NAME=flagforge-clean-qa` both rendered successfully. |
| `docker compose up --build -d` | **Passed** | Default stack recreated with generated names and scoped network; named volumes were retained. |
| `scripts/health-check.ps1` | **Passed** | All 10 long-running services healthy; both one-shot migration containers exited 0; HTTP checks passed for API, web, demo app, Flagsmith liveness and Collector health. |
| Alembic current | **Passed** | `009_encrypt_webhook_secrets (head)`. |
| Backend pytest in project container | **Passed** | 35 passed, one Starlette/httpx deprecation warning. |
| `npx tsc --noEmit` | **Passed** | Exit code 0. |
| `npm run build` | **Passed** | Next.js 16.4.6 production build generated all 20 app routes. |
| `npm audit` / `npm audit --omit=dev` | **Passed** | Both report zero known vulnerabilities. |
| Headed Playwright Chromium | **Passed** | 1 end-to-end workflow passed against the rebuilt production container and again against a fresh isolated checkout. |
| Clean-checkout installation | **Passed** | Committed `acd08d4` cloned separately, documented `setup.ps1` built and started the stack with a distinct Compose name/volumes; all service and HTTP health checks passed. |
| Supplemental `npx eslint src` | **Failed** | 34 existing source findings: 15 `set-state-in-effect`, 14 `exhaustive-deps`, 2 internal-navigation, 2 unescaped-text and 1 immutability. This was not weakened to obtain a pass. |

## Browser workflow

- Registered a disposable account, created an organization, project and custom environment; verified organization persistence after reload.
- Seeded synthetic demo fixtures in the disposable QA organization and confirmed the response identified them as local synthetic data.
- Opened all 18 existing routes, including the created project detail, and waited beyond loading states. Interacted with scanner/search, flag search/filter, synthetic Chaos Lab, dependency graph, monitoring, risk, incidents, cleanup preview, GitHub no-credentials state, settings and navigation.
- Confirmed Chaos Lab stated that it performed no remote flag mutation. The Production lock remained active.
- Checked a 390px mobile viewport for horizontal overflow.
- Logged out and back in; verified organization persistence. Uncaught browser page errors and HTTP 5xx responses: none.
- The first upgraded-app E2E attempt exposed two harness ordering issues (public auth-route sweep and home-page hydration). The test was corrected and the entire headed suite rerun successfully.

Screenshots, traces and test output are in the ignored `frontend/test-results/` and `frontend/playwright-report/` directories. These files contain synthetic QA data only and are not committed.

The fresh isolated checkout at `C:\Users\unbel\Downloads\FlagForge_CleanInstall_QA` also passed the headed Playwright run (1 passed, 32.6 seconds). The default project's named volumes were preserved; the fresh checkout created a separate set of volumes. Both installs ran on the same Windows/Docker Desktop host.

## Real and mocked integrations

- **Flagsmith real local API:** official 2.295.2 instance, pinned by digest. Existing evidence covers project/environment/flag discovery and synchronization, including Staging-only state change detection; Development and Production remained unchanged.
- **Flagsmith live webhook:** provider-signed test callback plus two actual Staging flag updates (enable and restore) were delivered to the private Compose alias, processed, and reconciled. Database evidence shows processed webhook events and completed webhook-triggered sync history. The test flag read back disabled; the temporary provider webhook was removed and the local webhook signing secret cleared. Provider retry behavior and outage recovery were not tested.
- **GitHub:** implementation is covered by mocked client, route and tenant tests. No GitHub credentials or authorized external QA repository were available; no external GitHub repository was contacted.
- **Redis worker:** durable Flagsmith sync/repository scan processing and restart recovery were verified previously; no additional worker job types were introduced.
- **OpenTelemetry:** prior end-to-end QA sent demo-app OTLP traffic through the Collector into authenticated, tenant-attributed storage and verified Monitor/Risk outputs. Demo telemetry is not customer traffic.
- **Chaos Lab:** synthetic demonstration only; no load and no provider mutation.
- **Rollback:** disabled with HTTP 501; no provider mutation is represented as successful.

## Remaining limitations

- A second physical machine was not available; clean install evidence covers a separate checkout with isolated volumes on this host only.
- Live GitHub authentication/PR lifecycle and race-safe provider rollback are unverified.
- Provider webhook retries, TLS/public ingress, backup restore, HA/load and independent penetration testing are unverified.
- The supplemental lint run reports 34 findings. TypeScript and production build pass; lint debt remains explicit.
