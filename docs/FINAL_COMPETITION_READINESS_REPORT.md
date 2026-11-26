# FlagForge Self-Hosted Flagsmith Verification Report

**Assessment date:** 2026-11-26
**Verdict:** The official local Flagsmith deployment and live FlagForge synchronization work. Several platform capabilities remain synthetic, unavailable, or unverified; this is not a production-readiness claim.

## Result summary

| Test area | Status | Evidence |
| --- | --- | --- |
| Docker services | **Passed** | All 10 long-running services healthy; `migrate` and `flagsmith-migrate-db` exited 0. The health script passed HTTP probes for API, web, demo app, Flagsmith, and Collector health. |
| Backend | **Passed** | `$env:PYTHONPATH='backend'; python -m pytest backend/tests/ -q`: 27 passed. Includes auth/JWT, RBAC/tenant boundaries, scanner/dependency graph, Flagsmith, webhook validation, chaos, telemetry, risk, and cleanup coverage. |
| Database | **Passed** | FlagForge Alembic revision `004_unify_dependency_node_enum`; Flagsmith migrations exited 0. The new PostgreSQL enum migration repaired the graph endpoint on the existing database. |
| Authentication | **Passed, scoped** | Playwright registered a QA account, created its isolated organization/project, and verified authentication persisted after reload. Backend auth tests passed. Invalid email validation displayed a readable field error after the UI fix. Logout/re-login was not repeated in Playwright. |
| Frontend routes | **Passed, route sweep** | Headed Playwright visited all 18 application paths, each returned HTTP 200 and rendered beyond its loading state. No page exceptions. The mobile Flags view had no horizontal overflow at 390px. |
| Browser workflows | **Passed with limits** | Registered an isolated QA account, created an organization/project with Development, Production, and Staging environments, searched synchronized flags, previewed a cleanup patch, and ran a synthetic Staging-only Chaos Lab scenario. Screenshots are in the QA workspace output folder, not the repository. |
| Flagsmith live connection | **Passed locally** | Official `docker.flagsmith.com/flagsmith/flagsmith:2.295.2` image pinned to digest `sha256:48905c664152d8ae2c843ec9cee72ff197e7caff6e91b959bb851a235915ea35`. FlagForge connection test returned `ok=true` and discovered one project. |
| Synchronization | **Passed live** | Local Flagsmith flags were created in the dedicated QA project and synchronized. FlagForge UI reported `12 created, 0 updated, 8 unchanged`; search found the new flags. An earlier live state change turned `flagforge_live_test` OFF only in Staging; FlagForge then showed Development ON, Production ON, Staging OFF. Replay sync was idempotent. |
| Webhooks | **Partial / live delivery skipped** | Internal HMAC validation tests pass. No webhook secret was configured and native Flagsmith delivery/signature compatibility was not exercised. |
| Chaos Lab | **Passed, synthetic only** | Ran a `staging` scenario in the isolated Playwright QA organization. The UI confirmed no traffic was sent and no remote flag changed. Production was locked. This is not a real load or provider-state chaos test. |
| Runtime monitoring | **Partial** | Local synthetic seeded metrics rendered (1,250 requests, 1.40% error rate, 142ms p95). Collector health passed, but Collector OTLP data is not bridged into the FlagForge telemetry store; live ingestion and percentile accuracy remain unverified. |
| Risk Engine / Release Guardian | **Passed, advisory only** | The seeded QA flag evaluated to a 62/100 HIGH risk score with manual approval required. The UI/API explicitly disable remote rollback; no rollback was attempted. |
| Dependency graph | **Passed after fix** | A real local QA scan stored four references; after migration 004, the live graph endpoint returned HTTP 200 with 6 nodes and 5 edges and the browser displayed them. |
| Cleanup Studio | **Passed, local preview** | Three synthetic stale-flag suggestions rendered and a local patch preview opened. GitHub PR creation remains unavailable and was not attempted. |
| TypeScript / production build | **Passed** | `npx tsc --noEmit` and `npm run build` exited 0; Next.js generated all 20 listed routes. |
| Compose configuration | **Passed** | `docker compose config --quiet` exited 0. |
| Security | **Partial** | Tests cover production secret checks, encryption/tamper handling, SSRF rules, webhook secret requirements, RBAC, and tenant isolation. The management key remained local, encrypted in FlagForge, and was never printed or committed. It was created with no expiry. TLS and external security review remain unverified. |

## Verified local integration

- Flagsmith `v2.295.2`, official image pinned by digest.
- Dedicated local Flagsmith organization/project: `FlagForge Competition Demo`; environments: Development, Production, and Staging.
- FlagForge connection uses `SELF_HOSTED` and `http://flagsmith:8000/api/v1` inside the Compose network.
- A Staging-only change to `flagforge_live_test` was detected by synchronization; Production remained ON.
- Additional local test flags: `new_dashboard`, `beta_analytics`, and `advanced_search`, all disabled by default.
- No Flagsmith Cloud or production instance, customer data, external repository, or GitHub PR was used.

## Fixes found during QA

- The flags page expected nested project/environment objects, but the API returns flat `project_name`, `environment_name`, and `is_production` fields. The page now supports the API shape; Playwright contract verification shows the project and all environment labels instead of “Unknown Project”/“Local”.
- FastAPI validation details arrived as an array and rendered as `[object Object]`. The API error formatter now displays readable field messages.
- The root `lib/` ignore rule excluded required frontend API/auth source from Git; the rule now allows `frontend/src/lib/`, and both required files are included.
- PostgreSQL graph writes failed because the migration gave `target_type` a different enum from `source_type`. Model metadata now shares `nodetype`; migration 004 repairs existing databases, and a regression test checks the shared enum name.
- Startup fixes documented in the setup guide include the missing frontend `public/` directory, JSON list syntax for `FLAGSMITH_ALLOWED_HOSTS`, and the missing `email-validator` runtime package.

## Findings by severity

### High

- The worker is still a healthy placeholder and logs that Redis job consumption is not implemented. Do not rely on background work.
- Collector health is not proof of end-to-end telemetry ingestion; OTLP data is not connected to FlagForge’s telemetry store.

### Medium

- Release Guardian remote rollback returns HTTP 501 and is intentionally disabled in the UI.
- GitHub PR creation is unavailable; cleanup only generated a local patch preview.
- Native Flagsmith webhook compatibility and live provider delivery remain unverified.
- The local Flagsmith management key has no expiry. It stayed local and encrypted, but should be revoked after the demo or replaced with a short-lived key before sharing.
- Flagsmith Cloud, external TLS, and a second-machine fresh-clone setup were not tested.

### Low

- Host ports 5433 and 6380 avoid existing local PostgreSQL/Redis listeners; container networking keeps the standard service ports.

## Evidence and artifacts

- Playwright route/browser screenshots: `outputs/flagforge-browser-qa/` in the QA workspace. Includes route captures, mobile Flags, synthetic Chaos Lab, cleanup preview, and the post-fix graph view.
- `scripts/health-check.ps1` lists service health and HTTP checks.
- Database revision: `004_unify_dependency_node_enum`.
- Runtime logs contain expected HTTP 422 responses from deliberately invalid email validation. Playwright recorded no page exceptions; route-navigation `ERR_ABORTED` entries were browser navigation cancellations.

## Readiness decision

The evidence supports **“official self-hosted Flagsmith deployed and live FlagForge synchronization verified locally.”** It does not support “fully working” or “production-ready.” Review [known limits and operations](INTEGRATIONS.md), [security notes](SECURITY.md), and [Docker setup](DOCKER_SETUP.md) before extending the deployment.
