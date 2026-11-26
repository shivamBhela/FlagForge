# Docker setup and operations

## Prerequisites

- Docker Desktop with Linux containers and Docker Compose v2.
- Windows x64 and PowerShell 7 for `setup.ps1`.
- At least 4 GB memory allocated to Docker.
- Available host ports: 3000, 8000, 8080, 8081, 13133, 4317, 4318, 8889, 5433 and 6380.

Setup detects port collisions and leaves existing listeners alone. FlagForge Redis maps to host port 6380 because other local projects often bind 6379.

## Start

```powershell
\.\setup.ps1
```

The script creates `.env` only when it is absent, generates local secrets without printing them, validates Compose quietly, runs `docker compose up --build -d`, then waits on health checks. An existing `.env` is not overwritten.

Manual operations:

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps --all
\.\scripts\health-check.ps1
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

All services use `flagforge-net`. FlagForge's API calls Flagsmith at `http://flagsmith:8000/api/v1`. Host browsers use published host ports, not Docker service DNS.

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

## Troubleshooting

- **Engine unavailable:** Start Docker Desktop and wait for `docker info` to show Client and Server. Do not delete WSL distributions or Docker data as a workaround.
- **Port in use:** Identify the owning process or choose another host port in ignored `.env`; never stop an unrelated service to make this stack fit.
- **API unhealthy:** Inspect API/migration/Postgres/Redis logs and `GET /api/v1/healthz`.
- **Flagsmith migration failure:** Inspect `flagsmith-migrate-db` and `flagsmith-postgres`; never point it at FlagForge Postgres.
- **FlagForge cannot connect to local Flagsmith:** Use `http://flagsmith:8000/api/v1`, verify an Organization API key, and check `FLAGSMITH_ALLOWED_HOSTS=flagsmith` in `.env`.
- **Memory pressure:** Reduce Docker build/runtime concurrency or stop only workloads approved by their owner. Do not terminate existing containers to force the demo stack to fit.
