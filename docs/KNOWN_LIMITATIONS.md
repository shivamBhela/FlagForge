# Known Limitations

This report separates live local verification from mocked, synthetic and unavailable integrations. See the [final readiness report](FINAL_COMPETITION_READINESS_REPORT.md) for current evidence.

## High

- **Production deployment hardening is incomplete.** This Compose stack is local-development oriented. Public TLS/ingress, production recovery procedures beyond the isolated restore drill, high availability, key rotation/expiry procedures and an independent security review have not been verified. Do not expose this stack publicly.
- **FlagForge's application PR workflow is unverified.** The repository branch `completion/final-readiness` is published, and draft PR [#1](https://github.com/shivamBhela/FlagForge/pull/1) is open against `main`. This is repository publication evidence, not a live test of FlagForge's own cleanup-to-PR workflow, which remains mock-tested only.

## Medium

- **Remote rollback is disabled for safety.** The pinned Flagsmith API accepts environment-scoped feature-state writes, but this deployment has not established a conditional-write/concurrency guarantee that would let FlagForge promise race-safe restoration after an incident. The Guardian endpoint returns HTTP 501 without mutating the provider. Risk evaluation remains advisory.
- **Worker job coverage is limited.** Redis Streams handlers cover Flagsmith sync and repository scans. Dependency graph generation, telemetry aggregation, risk evaluation and cleanup analysis remain synchronous local operations.
- **Login rate limiting is implemented and locally verified.** It depends on Redis, fails closed when Redis is unavailable, and has not had an independent security review or external load test.
- **Chaos Lab is synthetic.** It changes no provider state and sends no load. Its UI identifies the scenario as simulated and confines the scenario label to Staging.
- **Installation testing is same-host only.** A fresh isolated checkout with separate Compose volumes passed the documented setup, migrations, health checks and browser workflow on this Windows/Docker Desktop host. A second physical machine was not available.
- **Flagsmith retry semantics are not fully verified.** A real provider test event and real Staging flag changes were delivered and processed. Provider retry/backoff behavior under callback outage and duplicate provider retry delivery were not tested.
- **Flagsmith is disconnected in the latest local QA session.** The Integrations page showed no connected instance; this pass performed only empty-form validation, without sending a provider request. Earlier isolated Staging synchronization and signed webhook tests are historical and were not repeated. A new live round trip needs a valid Organization Management API token entered locally; no credential should be sent in chat.
- **Public hosting is paused by user direction to keep the budget at ₹0.** There is no public URL. Render's included bandwidth and pipeline limits can incur charges when exceeded, and a $0 spending cap was not verified; no Render resources were created.
- **Provider-specific rollback is unverified and disabled; FlagForge's own external GitHub cleanup/PR lifecycle is unverified.**

## Low

- The backend suite emits a Starlette/httpx test-client deprecation warning.
- Compose defaults use nonstandard local PostgreSQL and Redis host ports to avoid common service collisions; the setup script now checks configured host ports.
- Browser QA and scanner/chaos/cleanup examples use synthetic QA records where identified. They are not customer or production data.

## Explicitly unverified

- Live use of FlagForge's PR workflow, separate from the already verified repository publication and draft PR.
- Provider conditional-write semantics for rollback under concurrent changes.
- Flagsmith webhook delivery retries and outage recovery behavior.
- Public TLS, production recovery procedures beyond the isolated drill, multi-node deployment, production load and independent penetration testing.

## Latest local verification note (2026-11-28)

The Full Compose health check passed after a temporary Docker Desktop/WSL engine stall was recovered by restarting Docker Desktop. Ten long-running services were healthy, both migration jobs exited 0, and Alembic current/head were `009_encrypt_webhook_secrets`. Backend pytest (46), CLI pytest (12), frontend lint, TypeScript, production build (20 routes), npm audit (0 vulnerabilities), and headed Playwright (1 passed, 19.8s test / 25.6s total) passed. The current monitor view has no telemetry windows. Local synthetic Chaos output is not provider mutation or customer telemetry. An isolated backup/restore drill for both PostgreSQL databases passed in temporary tmpfs-backed instances; existing named volumes remained untouched. See the [local evidence index](../artifacts/evidence/EVIDENCE_INDEX.md) and [no-voice demo shot list](../artifacts/demo/VIDEO_SHOTLIST.md); both artifacts are ignored by Git and remain local.
