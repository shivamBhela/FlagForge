# Local Self-Hosted Quickstart

FlagForge’s complete local demonstration runs with Docker Compose and the official self-hosted Flagsmith service. The setup is local-only and is not production hardened.

## Requirements

- Docker Desktop using the Linux engine
- Docker Compose v2
- PowerShell 7 recommended on Windows

## Start FlagForge

From the repository root:

~~~powershell
.\setup.ps1 -Profile Full
.\scripts\health-check.ps1 -Profile Full
~~~

The setup script creates a local .env with generated values when one is absent. It preserves an existing .env and named Docker volumes.

Open the local URLs printed by setup for FlagForge, Flagsmith, API docs and the demo app. Do not change Production flags in the test setup.

To stop without deleting stored data:

~~~powershell
.\scripts\stop.ps1
~~~

Do not use docker compose down -v unless you intend to delete the application databases and Redis data.

## Connect a local Flagsmith project

1. Open the local Flagsmith service and finish its initial administrator setup.
2. Create a dedicated QA organization and project with Development and Staging environments.
3. Create a disposable test flag in Staging.
4. In Flagsmith organization settings, create an Organization Management API key with the shortest practical expiry.
5. In FlagForge, open Integrations, select Flagsmith Local and use the Compose service URL shown by the project configuration. The API container must reach Flagsmith through its service name, not localhost.
6. Test the connection, save it and run synchronization. The management key is stored server-side encrypted; do not paste it into browser variables or source files.
7. Verify the imported project, environments and flags.

An Organization Management API key is distinct from an environment SDK key and a Flagsmith dashboard password. See the [Flagsmith setup guide](FLAGSMITH_SETUP.md), [integration notes](INTEGRATIONS.md) and [security notes](SECURITY.md).

## Services and data

The Full profile includes the FlagForge frontend, API, worker, PostgreSQL, Redis, Collector and demo app, plus self-hosted Flagsmith, its separate PostgreSQL database and migration jobs. FlagForge does not share or query Flagsmith's database directly.

The latest recorded full-stack QA health check, from the separate `completion/final-readiness` branch, reported 10 long-running services healthy and both migration jobs exited successfully. The worker recovery check passed. That run did not reconnect Flagsmith or synchronize; prior Staging authentication/synchronization checks are historical evidence. These results do not certify a different branch or installation. See the [QA report](FINAL_COMPETITION_READINESS_REPORT.md) for exact fresh and historical evidence.

Chaos Lab is a synthetic Staging demonstration. It sends no load and does not mutate provider state. The latest Monitor session had no telemetry windows, although the authenticated OTLP ingestion pipeline is implemented and was previously exercised with demo-app traffic. Provider rollback remains disabled with an explicit HTTP 501 response and no provider mutation. Cleanup-to-PR code is implemented but live GitHub use is not verified. This project is not production-ready.

## Persistence and secrets

Named database and cache volumes persist when services stop. Keep local .env files and database dumps outside Git. Never publish environment SDK keys, Management API keys, passwords or session credentials.
