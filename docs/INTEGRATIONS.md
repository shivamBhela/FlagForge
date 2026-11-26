# Integrations status

## Flagsmith

Official self-hosted Flagsmith is the primary local demonstration target. FlagForge uses its Management API with `Authorization: Api-Key …`, discovers projects/environments/features/environment states, and stores encrypted credentials server-side. In Compose the API URL is `http://flagsmith:8000/api/v1`; the dashboard is published on host port 8081. Only describe live sync as verified when the running official instance was actually queried.

The API's `FLAGSMITH_ALLOWED_HOSTS` is an exact-host allowlist for private service DNS. It does not allow arbitrary private addresses, loopback, link-local, or metadata destinations.

## GitHub

Source scanning and local diff previews exist. GitHub App repository authorization, branch creation and pull request creation are not implemented; PR creation returns HTTP 501. A patch preview is not a pull request.

## OpenTelemetry

The Collector receives OTLP and exposes transformed Prometheus metrics. Demo-app instrumentation and verified Collector-to-FlagForge database ingestion are still outstanding. The Monitor/Risk UI must not describe synthetic aggregates as live telemetry.

## Redis and workers

Compose runs a real Redis service with a health probe. The `worker` service is still a placeholder and has no demonstrated queue consumption, retry or recovery behavior. Manual Flagsmith sync currently executes synchronously in the API.

## Chaos Lab and Release Guardian

Chaos Lab is synthetic staging-only and performs no remote mutation or verified restoration. Guardian risk assessment exists; remote Flagsmith rollback returns HTTP 501 until provider writes and read-after-write verification exist.

## Webhooks

FlagForge tests its configured HMAC request contract and replay protections. Native Flagsmith webhook compatibility has not been verified against live delivery.
