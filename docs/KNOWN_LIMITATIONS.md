# Known Limitations

This report separates live local verification from mocked, synthetic and unavailable integrations. See the [final readiness report](FINAL_COMPETITION_READINESS_REPORT.md) for current evidence.

## High

- **Production deployment hardening is incomplete.** This Compose stack is local-development oriented. Public TLS/ingress, backup and restore drills, high availability, key rotation/expiry procedures and an independent security review have not been verified. Do not expose this stack publicly.
- **GitHub PR creation is implemented but live use is unverified.** No GitHub App installation or authorized test repository credentials are configured. Authentication, repository listing and PR lifecycle are covered by mocked tests only; no external repository was contacted.

## Medium

- **Remote rollback is disabled for safety.** The pinned Flagsmith API accepts environment-scoped feature-state writes, but this deployment has not established a conditional-write/concurrency guarantee that would let FlagForge promise race-safe restoration after an incident. The Guardian endpoint returns HTTP 501 without mutating the provider. Risk evaluation remains advisory.
- **Worker job coverage is limited.** Redis Streams handlers cover Flagsmith sync and repository scans. Dependency graph generation, telemetry aggregation, risk evaluation and cleanup analysis remain synchronous local operations.
- **Chaos Lab is synthetic.** It changes no provider state and sends no load. Its UI identifies the scenario as simulated and confines the scenario label to Staging.
- **Clean-checkout installation is not yet evidenced.** The default local deployment is verified on this Windows/Docker Desktop host; the isolated fresh-checkout run remains pending. A second physical machine was not available.
- **Flagsmith retry semantics are not fully verified.** A real provider test event and real Staging flag changes were delivered and processed. Provider retry/backoff behavior under callback outage and duplicate provider retry delivery were not tested.
- **Provider-specific rollback and external GitHub lifecycle are unverified.** No remote rollback is enabled and no GitHub credentials were available.

## Low

- The backend suite emits a Starlette/httpx test-client deprecation warning.
- Compose defaults use nonstandard local PostgreSQL and Redis host ports to avoid common service collisions; the setup script now checks configured host ports.
- Browser QA and scanner/chaos/cleanup examples use synthetic QA records where identified. They are not customer or production data.

## Explicitly unverified

- GitHub App/token authentication against GitHub, authorized repository listing, actual branch/commit/PR creation and PR status refresh.
- Provider conditional-write semantics for rollback under concurrent changes.
- Flagsmith webhook delivery retries and outage recovery behavior.
- Public TLS, backup restore, multi-node deployment, production load and independent penetration testing.
