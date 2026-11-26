# Integrations status

## Flagsmith

Official self-hosted Flagsmith is the primary local demonstration target. FlagForge uses its Management API with `Authorization: Api-Key …`, discovers projects/environments/features/environment states, and stores encrypted credentials server-side. In Compose the API URL is `http://flagsmith:8000/api/v1`; the dashboard is published on host port 8081. Only describe live sync as verified when the running official instance was actually queried.

The API's `FLAGSMITH_ALLOWED_HOSTS` is an exact-host allowlist for private service DNS. It does not allow arbitrary private addresses, loopback, link-local, or metadata destinations.

## GitHub

Cleanup Studio supports organization-scoped GitHub access using either:

- A GitHub App installation. Set `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY` on the API service, install the App on the intended repositories with Metadata read, Contents read/write and Pull requests write, then connect its installation ID in Integrations. FlagForge mints an installation token for each request; it does not store or return the short-lived token. GitHub installation tokens expire after one hour ([GitHub authentication documentation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)).
- A fine-grained personal access token as a local testing alternative. Restrict it to the test repository and the same minimum repository permissions. FlagForge encrypts it at rest and never returns it to the frontend.

An organization admin lists authorized repositories and selects one. Cleanup Studio retrieves the exact UTF-8 source file, lets the reviewer edit it, computes the real diff, then verifies the base commit and file SHA again. PR creation requires explicit confirmation, creates a deterministic `flagforge/cleanup-…` branch, writes a single reviewed file change, opens a pull request, persists its number/URL/state, and can refresh state. It never writes to the default branch or merges. Retries check for an existing branch/commit/PR and refuse unexpected branch contents. The [GitHub PR API](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request) supports GitHub App installation tokens and fine-grained PATs with Pull requests write.

No GitHub credentials or authorized test repository are configured in this environment, so external repository listing and real PR creation remain **BLOCKED BY MISSING CREDENTIALS**. The app/PR flow is implemented and covered by mocked API and tenant tests only. No external GitHub repository has been contacted.

## OpenTelemetry

The demo app emits OTLP/HTTP JSON histograms to the Collector, which exports authenticated data to FlagForge's ingestion endpoint. The endpoint validates configured organization/project/environment/service attribution and persists request, error and histogram observations. Runtime Monitor and Risk Engine were verified with QA traffic. Missing telemetry is reported as insufficient data. Do not treat demo traffic as production measurements.

## Redis and workers

Compose runs Redis Streams with a consumer group, persisted job status, bounded retry/backoff and recovery of pending jobs after restart. Flagsmith sync and repository scan have worker handlers and were exercised. Other operations remain synchronous.

## Chaos Lab and Release Guardian

Chaos Lab is synthetic staging-only and performs no remote mutation or verified restoration. Guardian risk assessment exists; remote Flagsmith rollback returns HTTP 501 without changing provider state because safe concurrent-write semantics have not been established.

## Webhooks

Official Flagsmith documentation describes environment-level `FLAG_UPDATED` events signed as HMAC-SHA256 over the raw request body in `X-Flagsmith-Signature`. FlagForge verifies the signature, prevents replay and scopes synchronization to the connected tenant. Backend tests cover valid/invalid signatures and duplicate events. On the local pinned Flagsmith 2.295.2 Staging environment, the provider's signed test callback and two real test-flag updates were received, processed and synchronized. The flag was read back in its original disabled state; the temporary provider webhook was removed and its signing secret cleared from FlagForge.

Flagsmith 2.295.2 rejects URLs that resolve to internal/private addresses by default. Its pinned source supports an `SSRF_ALLOWED_HOSTS` exact-host allowlist; the local Compose configuration permits only the private DNS alias `api.flagforge.local` for callbacks. The alias resolves to the FlagForge API service only on the Compose network. The Flagsmith SSRF guard remains enabled for every other hostname and destination ([pinned validator](https://github.com/Flagsmith/flagsmith/blob/v2.295.2/api/core/validators.py), [pinned network check](https://github.com/Flagsmith/flagsmith/blob/v2.295.2/api/core/network.py)). Use `http://api.flagforge.local:8000/api/v1/webhooks/flagsmith/{connection_id}`, set the same random HMAC secret in FlagForge and the environment webhook, and test only against QA Staging. Live delivery was verified for this local deployment; verify it again in each deployment environment. Do not use a public relay.

## Worker job scope

The Redis worker currently handles durable Flagsmith sync and repository scan jobs with status, retries and restart recovery. Dependency graphs, telemetry aggregation, risk evaluation and cleanup summaries are lightweight local database operations; keeping these synchronous avoids unnecessary queue state and stale results. Webhook event handling currently verifies and persists the event, then runs targeted reconciliation in the request path. A future high-volume deployment should queue that reconciliation with an idempotency key and acknowledge only after durable enqueue.
