# Known Limitations

This file distinguishes working local demonstrations from incomplete production capabilities. See the [final competition readiness report](FINAL_COMPETITION_READINESS_REPORT.md) for evidence and test dates.

## High

- **GitHub PR workflow — not implemented.** Cleanup Studio can show a local patch preview only. There is no GitHub App installation, repository authorization, branch/commit/PR API flow, PR persistence, or status refresh. GitHub credentials are not configured. The endpoint returns HTTP 501 and does not mutate a repository.
- **Remote rollback — disabled for safety.** Release Guardian provides deterministic risk assessment and recommendations. It does not write Flagsmith state. The endpoint returns HTTP 501 until an environment-scoped provider mutation, approval, audit, locking and read-after-write flow is verified against the pinned Flagsmith instance.
- **Production deployment hardening — incomplete.** Compose is intended for local demonstration. External TLS, public ingress controls, durable backup/restore drills, key rotation/expiry policy, HA and independent penetration testing are not evidenced. Do not expose this stack publicly.

## Medium

- **Native Flagsmith webhook — not live-verified.** Provider documentation specifies environment-level `FLAG_UPDATED` delivery signed by HMAC-SHA256 over the raw UTF-8 body in `X-Flagsmith-Signature`. FlagForge validates the contract and has unit coverage. During browser QA, Flagsmith 2.295.2 rejected the local receiver URL as an internal/private network target before its test request was sent; no webhook was created and no delivery is claimed. The provider's SSRF protection remains enabled, and no public relay was used.
- **Worker scope is limited.** Redis Streams jobs currently execute Flagsmith sync and repository scans, with durable status, retry/backoff and restart recovery. Dependency graph processing, telemetry aggregation, risk evaluation and cleanup analysis remain synchronous.
- **Chaos Lab is a simulation.** It does not send load, change a Flagsmith flag or prove state restoration.
- **Reuse beyond this machine is unproven.** Setup and troubleshooting docs exist, but a fresh clone/installation on a second machine was not tested. Host pytest also requires installing backend dependencies; containerized pytest passed.
- **GitHub configuration is absent.** The local `.env` contains no configured GitHub App ID or private key. No external repository was accessed.

## Low

- The backend suite reports a Starlette deprecation warning about its `httpx` test-client integration.
- Default host ports 5433 and 6380 are nonstandard to avoid clashing with common existing PostgreSQL/Redis services.
- Browser QA used synthetic sample records for scanner/chaos/cleanup screens where noted; those must not be represented as live provider or customer data.

## Explicitly unverified

- Native webhook live delivery, duplicate provider retry behavior and provider-side failure retry. The local UI's private-network URL rejection was observed in Chrome, but no callback request was sent.
- GitHub authentication, branch creation, commit, PR lifecycle and webhooks.
- Flagsmith provider-side rollback mutation and exact environment-state restoration.
- Public TLS, backup restoration, multi-node deployment, load testing and external security review.
