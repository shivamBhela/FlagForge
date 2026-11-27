# Known Limitations

This report separates live local verification from mocked, synthetic and unavailable integrations. See the [final readiness report](FINAL_COMPETITION_READINESS_REPORT.md) for current evidence.

## High

- **Production deployment hardening is incomplete.** This Compose stack is local-development oriented. Public TLS/ingress, backup and restore drills, high availability, key rotation/expiry procedures and an independent security review have not been verified. Do not expose this stack publicly.
- **FlagForge's application PR workflow is unverified.** The repository branch `completion/final-readiness` is published, and draft PR [#1](https://github.com/shivamBhela/FlagForge/pull/1) is open against `main`. This is repository publication evidence, not a live test of FlagForge's own cleanup-to-PR workflow, which remains mock-tested only.

## Medium

- **Remote rollback is disabled for safety.** The pinned Flagsmith API accepts environment-scoped feature-state writes, but this deployment has not established a conditional-write/concurrency guarantee that would let FlagForge promise race-safe restoration after an incident. The Guardian endpoint returns HTTP 501 without mutating the provider. Risk evaluation remains advisory.
- **Worker job coverage is limited.** Redis Streams handlers cover Flagsmith sync and repository scans. Dependency graph generation, telemetry aggregation, risk evaluation and cleanup analysis remain synchronous local operations.
- **Request rate limiting is not implemented.** This leaves brute-force protection incomplete and should be addressed before shared or public deployment.
- **Chaos Lab is synthetic.** It changes no provider state and sends no load. Its UI identifies the scenario as simulated and confines the scenario label to Staging.
- **Installation testing is same-host only.** A fresh isolated checkout with separate Compose volumes passed the documented setup, migrations, health checks and browser workflow on this Windows/Docker Desktop host. A second physical machine was not available.
- **Flagsmith retry semantics are not fully verified.** A real provider test event and real Staging flag changes were delivered and processed. Provider retry/backoff behavior under callback outage and duplicate provider retry delivery were not tested.
- **A fresh Flagsmith login could not be verified.** The supplied account was rejected by the local Flagsmith login page on one attempt. Earlier isolated Staging synchronization and webhook tests passed; confirm the account before repeating a live provider round trip.
- **Public hosting is not configured or deployed.** There is no public URL; provider account access and any cost approval are prerequisites.
- **Provider-specific rollback is unverified and disabled; FlagForge's own external GitHub cleanup/PR lifecycle is unverified.**

## Low

- The backend suite emits a Starlette/httpx test-client deprecation warning.
- Compose defaults use nonstandard local PostgreSQL and Redis host ports to avoid common service collisions; the setup script now checks configured host ports.
- Browser QA and scanner/chaos/cleanup examples use synthetic QA records where identified. They are not customer or production data.

## Explicitly unverified

- Live use of FlagForge's PR workflow, separate from the already verified repository publication and draft PR.
- Provider conditional-write semantics for rollback under concurrent changes.
- Flagsmith webhook delivery retries and outage recovery behavior.
- Public TLS, backup restore, multi-node deployment, production load and independent penetration testing.
