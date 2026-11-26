# Integrations status

## Flagsmith

Official self-hosted Flagsmith is the primary local demonstration target. FlagForge uses its Management API with `Authorization: Api-Key …`, discovers projects/environments/features/environment states, and stores encrypted credentials server-side. In Compose the API URL is `http://flagsmith:8000/api/v1`; the dashboard is published on host port 8081. Only describe live sync as verified when the running official instance was actually queried.

The API's `FLAGSMITH_ALLOWED_HOSTS` is an exact-host allowlist for private service DNS. It does not allow arbitrary private addresses, loopback, link-local, or metadata destinations.

## GitHub

Source scanning and local diff previews exist. GitHub App repository authorization, branch creation and pull request creation are not implemented; PR creation returns HTTP 501. GitHub App ID/private key are not configured locally. A patch preview is not a pull request, and no repository was changed.

## OpenTelemetry

The demo app emits OTLP/HTTP JSON histograms to the Collector, which exports authenticated data to FlagForge's ingestion endpoint. The endpoint validates configured organization/project/environment/service attribution and persists request, error and histogram observations. Runtime Monitor and Risk Engine were verified with QA traffic. Missing telemetry is reported as insufficient data. Do not treat demo traffic as production measurements.

## Redis and workers

Compose runs Redis Streams with a consumer group, persisted job status, bounded retry/backoff and recovery of pending jobs after restart. Flagsmith sync and repository scan have worker handlers and were exercised. Other operations remain synchronous.

## Chaos Lab and Release Guardian

Chaos Lab is synthetic staging-only and performs no remote mutation or verified restoration. Guardian risk assessment exists; remote Flagsmith rollback returns HTTP 501 until provider writes and read-after-write verification exist.

## Webhooks

Official Flagsmith documentation specifies environment-level `FLAG_UPDATED` events signed as HMAC-SHA256 over the raw request body in `X-Flagsmith-Signature`. FlagForge implements that signature contract, replay protection and connection-scoped synchronization; unit tests cover valid/invalid signatures and duplicates. The local Flagsmith Staging environment was not configured to deliver a live webhook during QA, so provider delivery remains unverified. Configure a Staging webhook only after setting the same random secret in FlagForge; never omit signature validation. See [Flagsmith webhook documentation](https://github.com/Flagsmith/flagsmith-docs/blob/main/docs/advanced-use/system-administration.md).
