# FlagForge + Self-Hosted Flagsmith

This repository runs the official Flagsmith service beside FlagForge. It uses Flagsmith as the feature-flag source of truth and synchronizes its projects, environments, features, and environment states into FlagForge.

## Quick start (Windows)

Install and start Docker Desktop with the Linux engine, then run:

```powershell
.\setup.ps1
```

Setup defaults to the lower-memory Core stack. To open FlagForge, either choose `-Profile Dashboard` on a fresh start or add the frontend with `docker compose --profile dashboard up --build -d web`; to add the Collector and demo app, run `docker compose --profile observability up --build -d otel-collector demo-app`. `-Profile Dashboard`, `-Profile Observability`, and `-Profile Full` select those combinations on a fresh start.

The setup script creates a local-only `.env` with generated secrets when one is absent, validates Compose, builds and starts the stack, then checks service health. It does not overwrite an existing `.env` or remove volumes. Once the relevant profile is running, open:

- FlagForge: <http://localhost:3000>
- Official Flagsmith: <http://localhost:8081>
- FlagForge API docs: <http://localhost:8000/api/v1/docs>
- Demo app (Observability profile): <http://localhost:8080>

To stop the stack without deleting persisted data:

```powershell
.\scripts\stop.ps1
```

To check the running services and migrations again:

```powershell
.\scripts\health-check.ps1
```

The database and cache host mappings default to `5433` and `6380`. Containers use the normal Compose service addresses (`postgres:5432`, `redis:6379`, and `flagsmith:8000`). If a configured host port is already in use, change it in `.env` before running setup.

## Connect the local Flagsmith instance

1. Open Flagsmith at `http://localhost:8081` and create a dedicated local organization and project.
2. Add Development and Staging environments and a test feature flag.
3. In organization settings, create a Management API key with the shortest practical expiry.
4. In FlagForge, register/sign in, select an organization, and open **Integrations**.
5. Choose **Flagsmith Local** and use `http://flagsmith:8000/api/v1` as the base URL. That hostname is reachable from the FlagForge API container; do not use `localhost` there.
6. Test the connection, save it, and select **Sync Now**. The token is sent to the backend and stored encrypted; it is not returned to the browser.
7. Confirm the projects and flags under **Feature Flags**.

See [FlagSmith setup](docs/FLAGSMITH_SETUP.md), [integration details](docs/INTEGRATIONS.md), and [security notes](docs/SECURITY.md) for configuration and boundaries.

## Services and persistence

The Compose project has seven FlagForge services (`web`, `api`, `worker`, `postgres`, `redis`, `otel-collector`, `demo-app`), three long-running Flagsmith services (`flagsmith`, `flagsmith-postgres`, `flagsmith-task-processor`), and two one-shot database migration jobs. Flagsmith has a separate PostgreSQL service and volume; it does not share FlagForge's schema or database.

The worker processes Redis Streams jobs for Flagsmith synchronization and repository scanning; other analyses are synchronous. Demo-app OTLP metrics flow through the Collector into FlagForge's authenticated telemetry store and Risk Engine. Chaos Lab runs synthetic simulations only and does not change Flagsmith state. Release Guardian rollback remains disabled and returns HTTP 501. Cleanup-to-GitHub PR workflow is implemented but has only mocked verification; the repository's own draft PR is a separate publication workflow. Prior local Flagsmith Staging sync and webhook tests passed, but live provider access was not reverified in the latest QA run. See the [end-to-end report](docs/END_TO_END_TEST_REPORT.md) and [readiness report](docs/FINAL_COMPETITION_READINESS_REPORT.md) for dated evidence.

## Lifecycle and data

The named database volumes persist across `docker compose down` and `scripts/stop.ps1`. Do not use `docker compose down -v` unless intentionally deleting both local application databases and Redis data. The stop script only stops the services and retains volumes.

Never commit `.env`, API keys, or generated local secrets. This Compose configuration is for local development/demo use; TLS, high availability and production operations are not configured. A backup procedure and safe isolated restore-verification instructions are in [Docker setup](docs/DOCKER_SETUP.md); restore has not been drilled.
