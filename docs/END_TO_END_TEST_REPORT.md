# End-to-End Test Report

**Run date:** 2026-11-26
**Target:** Local Windows Docker Desktop deployment at `http://localhost:3000`
**Data scope:** Dedicated FlagForge QA user/org/project and Staging telemetry; existing named Docker volumes retained.

## Commands and results

| Command or workflow | Result | Evidence |
| --- | --- | --- |
| `docker compose config --quiet` | Passed | Exit code 0. |
| `docker compose up --no-deps --build --force-recreate migrate` | Passed | FlagForge migration container exited 0. |
| `docker compose exec -T api alembic -c alembic.ini current` | Passed | `007_scan_job_idempotency (head)`. |
| Flagsmith migration container | Passed | `flagsmith-migrate-db` exited 0; database is separate. |
| `scripts/health-check.ps1` | Passed in completed deployment run | Checks all 10 long-running containers, both migration exit codes, and API/web/demo/Flagsmith/Collector HTTP health. Final `docker compose ps --all` showed all 10 long-running services healthy and migration jobs exited 0. |
| `docker compose run --rm --no-deps --build api python -m pytest tests/ -q` | Passed | **31 passed**, 1 Starlette deprecation warning. |
| `$env:PYTHONPATH='backend'; python -m pytest backend/tests/ -q` on host | Failed at test collection (environment dependency) | Host Python has no `redis` package. The same suite ran in the project API image and passed. This is a host setup failure, not a passing test run. |
| `npx tsc --noEmit` | Passed | Exit code 0. |
| `npm run build` | Passed | Exit code 0; Next.js generated the 20 application routes. |
| Worker restart recovery | Passed | Queued a repository scan with worker stopped (PENDING), restarted worker, observed COMPLETED, attempts=1 and one stored code reference. |
| OTLP end-to-end | Passed | Demo app emitted request histograms via Collector to authenticated FlagForge ingestion; successful and controlled HTTP 500 requests persisted. The QA smoke run reported 76 requests, 75 successes, one error, and persisted histogram latency. |
| Risk with live QA telemetry | Passed | Risk response reported telemetry confidence `SUFFICIENT` and computed an advisory band/score from persisted observations. |
| Official local Flagsmith sync | Passed | Discovered local project; synchronized real test flags; a Staging-only test-state change was detected; replay sync was idempotent. No production instance used. |
| Headed Chromium browser QA | Passed with integration limits below | All 18 routes exercised beyond loading; functional workflows and console exception review performed. Screenshots stored in the QA workspace. |

## Browser interactions

- Registered an isolated FlagForge test account; logged in, logged out and back in; verified session restoration after reload.
- Created a dedicated organization, project, default environments and a custom non-production environment.
- Visited and interacted with Projects, Flags, Scanner, Dependencies, Chaos, Monitor, Guardian, Incidents, Cleanup, Integrations, Policies and Settings; visited auth and creation routes as well.
- Ran the built-in sample scanner and observed stored references; searched for a known flag reference and an unmatched search term.
- Loaded dependency graph (six nodes, five edges) after the PostgreSQL enum repair.
- Ran a labeled synthetic Staging-only Chaos Lab scenario; UI explicitly said no traffic or remote flag mutation occurred and Production remained locked.
- Inspected cleanup candidates and opened a local patch preview; GitHub PR unavailable.
- Inspected empty integration state in the browser-only org; live Flagsmith connection/sync evidence came from the separate dedicated integration test project, not this new org.
- Verified empty telemetry is shown as insufficient/no data, then emitted actual demo-app traffic to a QA Staging telemetry project.
- Checked the 390px mobile viewport; the inspected page had no horizontal overflow. Browser console page errors were empty.

## External integration classification

- **Live local:** Flagsmith API sync; Redis Streams worker and recovery; OTLP demo-app → Collector → FlagForge persistence → risk evaluation.
- **Mocked/contract-tested:** webhook signature and replay validation in backend tests; provider adapter mocks.
- **Not live-tested:** Flagsmith’s native configured webhook delivery; GitHub API/PR; remote rollback.
- **Demo-only:** Chaos simulation and seeded example content.

## Browser artifacts

QA workspace: `outputs/flagforge-browser-qa/`. Captures include `home.png`, `register.png`, `login.png`, route views, `flags-mobile-390.png`, `dependencies-after-fix.png`, `chaos.png`, `cleanup-preview.png`, and settings. These are QA artifacts outside the application repository and contain only local test data.

## Failures and their disposition

- **Host backend pytest collection:** failed due to missing host `redis` dependency. Retested in the project API container with dependencies installed; 31 tests passed.
- **Stale prior migration container:** had exit code 255 from an older image, which made the health script’s one-shot migration condition fail. Rebuilt/recreated the migration service; it exited 0, then current revision verified at head. No volume or database reset was used.
- **Initial OTLP test attempt:** Collector default compression yielded API HTTP 400. Collector exporter was configured with JSON encoding and no compression; subsequent real demo traffic was accepted and persisted.

## Limitations

Native Flagsmith webhook endpoint setup/delivery, GitHub PR creation, remote rollback, second-machine clean installation, public TLS and backup/restore are not verified. See [known limitations](KNOWN_LIMITATIONS.md) and the [final competition report](FINAL_COMPETITION_READINESS_REPORT.md).
