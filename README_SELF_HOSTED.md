# FlagForge + Self-Hosted Flagsmith

This repository runs the official Flagsmith service beside FlagForge. It uses Flagsmith as the feature-flag source of truth and synchronizes its projects, environments, features, and environment states into FlagForge.

## Quick start (Windows)

Install and start Docker Desktop with the Linux engine, then run:

```powershell
.\setup.ps1
```

Setup defaults to the lower-memory Core stack. To add the frontend, run `docker compose --profile dashboard up --build -d web`; to add the Collector and demo app, run `docker compose --profile observability up --build -d otel-collector demo-app`. `-Profile Dashboard`, `-Profile Observability`, and `-Profile Full` select those combinations on a fresh start.

The setup script creates a local-only `.env` with generated secrets when one is absent, validates Compose, builds and starts the stack, then checks service health. It does not overwrite an existing `.env` or remove volumes. Open:

- FlagForge: <http://localhost:3000>
- Official Flagsmith: <http://localhost:8081>
- FlagForge API docs: <http://localhost:8000/api/v1/docs>
- Demo app: <http://localhost:8080>

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

The current verified worker is a placeholder: it does not consume Redis jobs. The Collector has a health endpoint but its data is not wired into FlagForge's metric store. Chaos Lab runs synthetic simulations only; it does not change Flagsmith state. Release Guardian remote rollback and GitHub PR creation are unavailable (HTTP 501). See the [verification report](docs/FINAL_COMPETITION_READINESS_REPORT.md) for current evidence.

## Lifecycle and data

The named database volumes persist across `docker compose down` and `scripts/stop.ps1`. Do not use `docker compose down -v` unless intentionally deleting both local application databases and Redis data. The stop script only stops the services and retains volumes.

Never commit `.env`, API keys, or generated local secrets. This Compose configuration is for local development/demo use; TLS, backups, resource hardening, and production operations are not configured.
