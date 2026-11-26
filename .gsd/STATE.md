# FlagForge Project State

## Current position

- **Status:** Local FlagForge + official self-hosted Flagsmith works for verified flows. Platform readiness remains partial; no production-readiness claim.
- **Assessment date:** 2026-11-26.
- **Docker:** 10 long-running containers healthy. FlagForge and Flagsmith migration services each exited 0. No volumes were deleted.
- **Database:** FlagForge Alembic is `007_scan_job_idempotency (head)`; Flagsmith has its separate PostgreSQL and migration history.
- **Backend:** 31 tests passed in the API image; one Starlette/httpx deprecation warning. Host test collection lacks the `redis` package; container run has complete project dependencies.
- **Frontend:** TypeScript check and Next production build passed (20 application routes).
- **Live local integrations:** Flagsmith sync/state-change detection; Redis job processing/restart recovery; demo-app OTLP through Collector to persisted telemetry and Risk Engine.

## Verified implementation

- Seven FlagForge services plus Flagsmith application, separate database, task processor and migrations are orchestrated by Compose.
- Worker supports Redis Streams jobs for Flagsmith sync and repository scanning with persisted status, retries/backoff, pending recovery and graceful shutdown.
- Authenticated OTLP/HTTP JSON histogram ingestion persists QA Staging metrics with organization/project/service attribution. Aggregation merges buckets before computing latency percentiles. Missing telemetry is insufficient rather than healthy.
- Official Flagsmith v2.295.2 image remains pinned by digest. Live project/flag sync and a Staging-only state change were observed; Development and Production remained unchanged.
- Headed Chromium exercised all 18 routes and real browser workflows; screenshots are in the QA workspace `outputs/flagforge-browser-qa/`.
- Backend suite: 31 passed; `npx tsc --noEmit` passed; `npm run build` passed; Compose config and migrations passed.
- New detailed evidence: `docs/END_TO_END_TEST_REPORT.md`, `docs/FINAL_COMPETITION_READINESS_REPORT.md`, `docs/KNOWN_LIMITATIONS.md`.

## Remaining limitations

- Native Flagsmith webhook contract matches provider docs and has automated validation/replay tests, but no live configured Flagsmith delivery was run.
- GitHub App PR workflow is not implemented; local diff preview only and endpoint returns HTTP 501. No GitHub App credentials are present.
- Remote Flagsmith rollback remains disabled with HTTP 501; no provider mutation is faked.
- Worker currently runs Flagsmith sync and repository scan only. Other analyses remain synchronous.
- Chaos Lab is synthetic and staging-only; it sends no load or remote flag mutation.
- Clean install on a second host, TLS/external exposure, backups/restore, key expiry/rotation and independent security review are unverified.

## Latest QA snapshot

An older migration container had failed with exit 255; it was rebuilt/recreated and exited 0. Current revision was verified at head. Earlier initial OTLP attempt returned HTTP 400 under Collector gzip defaults; JSON/no-compression configuration now passes real QA traffic. The host pytest command fails at collection without the `redis` package, while the API image test command reports 31 passing tests.

## Next work

Configure and deliver a signed webhook from the isolated local Flagsmith Staging environment if local dashboard credentials are available. Keep GitHub PR and rollback disabled until credential/provider contracts and safe implementation are available. Do not revoke a still-used local Flagsmith key without replacing and verifying it first. Do not expose the local deployment publicly.
