# Docker setup and operations

## Prerequisites

- Docker Desktop with Linux containers and Docker Compose v2.
- Windows x64 and PowerShell 7 for `setup.ps1`.
- At least 4 GB memory allocated to Docker for the Dashboard profile. On an 8 GB PC with a smaller Docker VM limit, use Core first; the prior full-stack run approached 3.58 GB.
- Available localhost ports: 3000, 8000, 8080, 8081, 13133, 4317, 4318, 8889, 5433 and 6380.

Setup reads configured host ports from `.env`, detects collisions on those ports, and leaves existing listeners alone. FlagForge Redis maps to host port 6380 because other local projects often bind 6379. The setup defaults are 3000, 8000, 8080, 8081, 5433 and 6380; Collector ports are fixed at 13133, 4317, 4318 and 8889.

The Compose project name defaults to `flagforge`. Compose scopes generated container names, network names and named volumes to that project. To run a separate checkout without sharing data, set a unique `COMPOSE_PROJECT_NAME` in its `.env` or the invoking process before running setup. Do not reuse a project name if the intent is to isolate its databases.

## Start

```powershell
.\setup.ps1 -Profile Dashboard
```

Available profiles:

| Command | Services added to the core |
| --- | --- |
| `./setup.ps1 -Profile Core` | API, worker, PostgreSQL, Redis and self-hosted Flagsmith only |
| `./setup.ps1 -Profile Dashboard` | Core plus Next.js frontend |
| `./setup.ps1 -Profile Observability` | Core plus OpenTelemetry Collector and demo app |
| `./setup.ps1 -Profile Full` | Core plus frontend, Collector and demo app |

Compose services in optional profiles remain available; omitting a profile does not remove their images, containers, or data. `setup.ps1` defaults to Core. From a running Core stack, add the dashboard with `docker compose --profile dashboard up --build -d web`, or add telemetry with `docker compose --profile observability up --build -d otel-collector demo-app`.

The script creates `.env` only when it is absent, generates local secrets without printing them, validates Compose quietly, runs `docker compose up --build -d`, then waits on health checks. An existing `.env` is not overwritten.

Manual operations:

```powershell
docker compose config --quiet
docker compose --profile dashboard up --build -d
docker compose ps --all
.\scripts\health-check.ps1 -Profile Dashboard
```

## Service and port inventory

| Service | Host URL/port | Data |
| --- | --- | --- |
| FlagForge web | `http://localhost:3000` | None |
| FlagForge API | `http://localhost:8000` | `flagforge_postgres_data` |
| FlagForge Alembic migration | One-shot container | FlagForge Postgres |
| FlagForge worker | Internal service | Redis Streams consumer for Flagsmith sync and repository scan jobs; durable status and restart recovery |
| FlagForge PostgreSQL | Host 5433, container 5432 | `flagforge_postgres_data` |
| FlagForge Redis | Host 6380, container 6379 | `flagforge_redis_data` |
| OTel Collector | OTLP 4317/4318; metrics 8889; health 13133 | None |
| Demo app | `http://localhost:8080` | None |
| Official Flagsmith dashboard/API | `http://localhost:8081` | `flagsmith_postgres_data` |
| Flagsmith PostgreSQL | Internal only | `flagsmith_postgres_data` |
| Flagsmith migration | One-shot container | Flagsmith Postgres |
| Flagsmith task processor | Internal service | Flagsmith application |

All services use the project-scoped Compose network whose logical key is `flagforge-net`. FlagForge's API calls Flagsmith at `http://flagsmith:8000/api/v1`. Host browsers use published host ports, not Docker service DNS. The named volume keys in this table are Compose keys; the actual volume names include the project prefix.

## Health and logs

```powershell
\.\scripts\health-check.ps1
docker compose logs --tail 200 api
docker compose logs --tail 200 worker
docker compose logs --tail 200 flagsmith
docker compose logs --tail 200 flagsmith-task-processor
docker compose logs --tail 200 postgres redis otel-collector
```

The health script checks service/container state, configured Docker healthchecks, successful one-shot migrations and HTTP responses from FlagForge API/web/demo, Flagsmith liveness and Collector health. A healthy process does not by itself prove Management API sync or task execution; follow the live integration instructions. Worker jobs currently cover Flagsmith sync and repository scanning; other analysis remains synchronous.

```powershell
docker compose exec api alembic -c alembic.ini current
docker compose ps --all migrate flagsmith-migrate-db
```

## Stop and preserve data

```powershell
\.\scripts\stop.ps1
```

This stops only the current Compose project. It does not remove volumes or affect unrelated containers. Restart with `docker compose up -d`.

`docker compose down` removes this project's containers/network but retains named volumes by default. Do not use `docker compose down --volumes` unless intentionally deleting both application databases. Back up before any destructive operation.

## Safe database backup and restore

Back up both databases before upgrades or planned changes. These commands write custom-format dumps to a local `backups` directory; treat the files as sensitive because they contain application data. The commands do not print database passwords or remove volumes.

```powershell
New-Item -ItemType Directory -Force backups | Out-Null
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backups/flagforge-postgres.dump
if ($LASTEXITCODE -ne 0) { throw 'FlagForge database dump failed; do not proceed with an upgrade.' }
docker compose exec -T flagsmith-postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backups/flagsmith-postgres.dump
if ($LASTEXITCODE -ne 0) { throw 'Flagsmith database dump failed; do not proceed with an upgrade.' }
```

Keep the two dumps separate and outside Git. A successful `pg_dump` exit code is required for each command. Store an additional copy in access-controlled storage before relying on it as disaster recovery.

To verify a dump without overwriting the running databases, first create a separate, isolated Compose project with a distinct `COMPOSE_PROJECT_NAME` and its own `.env`/volumes. Start only its database service, create a new empty database in that isolated PostgreSQL instance, then restore the corresponding dump into that new database with `pg_restore --no-owner --dbname <new-database>`. Never restore over the live `flagforge` or `flagsmith` database as a test. Confirm the restored schema/data in the isolated project before considering the backup procedure verified. This repository's routine QA did not perform a restore drill.

To restore a real deployment, stop application writers, take a fresh backup of the target, and restore each dump only into the explicitly selected target database under an approved maintenance procedure. Restore is destructive to the target database contents and must not be run against a shared or production database without a separate backup and authorization.

## Troubleshooting

- **Engine unavailable:** Start Docker Desktop and wait for `docker info` to show Client and Server. Do not delete WSL distributions or Docker data as a workaround.
- **Port in use:** Identify the owning process or choose another host port in ignored `.env`; never stop an unrelated service to make this stack fit.
- **API unhealthy:** Inspect API/migration/Postgres/Redis logs and `GET /api/v1/healthz`.
- **Flagsmith migration failure:** Inspect `flagsmith-migrate-db` and `flagsmith-postgres`; never point it at FlagForge Postgres.
- **FlagForge cannot connect to local Flagsmith:** Use `http://flagsmith:8000/api/v1`, verify an Organization API key, and check `FLAGSMITH_ALLOWED_HOSTS=flagsmith` in `.env`.
- **Memory pressure:** Reduce Docker build/runtime concurrency or stop only workloads approved by their owner. Do not terminate existing containers to force the demo stack to fit.

## Network exposure and optional providers

By default, published host ports bind to `127.0.0.1`. Browsers on this machine can access the dashboards; Docker services communicate over `flagforge-net`. Do not change the bind address to `0.0.0.0` unless you have intentionally configured and reviewed restricted ingress and TLS.

The local Flagsmith callback allowlist includes only the exact Compose-only DNS alias `api.flagforge.local` via `SSRF_ALLOWED_HOSTS`. It resolves to the API only on the Compose network; upstream SSRF checks remain active for every other destination. The signed test callback and Staging-only flag update/restore were live-verified. Do not add private network ranges, loopback, metadata destinations or a public relay.

Optional GitHub App configuration uses `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY` in the ignored `.env`. Alternatively, the Integrations screen accepts an authorized fine-grained PAT, encrypted by the API. Scope access to one QA repository with Metadata read, Contents read/write and Pull requests write. Never use a production repository for initial verification.
