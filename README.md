# FlagForge

FlagForge is a feature-flag release intelligence prototype built on the official [self-hosted Flagsmith](https://github.com/Flagsmith/flagsmith) platform. Flagsmith and FlagForge have separate PostgreSQL databases and communicate through the supported Flagsmith Management API.

## Start the local demonstration

Requirements: Windows x64, Docker Desktop with Linux containers, Docker Compose v2, PowerShell 7, and 4 GB or more of memory available to Docker for the Dashboard profile. On smaller Docker VM limits, start Core first.

```powershell
.\setup.ps1 -Profile Dashboard
```

Use `./setup.ps1` or `./setup.ps1 -Profile Core` for the lower-memory API/provider session without Next.js. From an already running Core stack, start the frontend with `docker compose --profile dashboard up --build -d web`. Add observability and the demo app only when needed with `docker compose --profile observability up --build -d otel-collector demo-app`. `./setup.ps1 -Profile Full` selects both optional profiles on a fresh start. Profiles do not remove services or data.

If `.env` is absent, setup generates unique local secrets without displaying them. It validates Compose, builds and starts the combined stack, then checks services. Existing `.env` files are preserved.

- Flagsmith dashboard: [http://localhost:8081](http://localhost:8081)
- FlagForge dashboard: [http://localhost:3000](http://localhost:3000)
- FlagForge API docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- Demo app: [http://localhost:8080](http://localhost:8080)

Create a dedicated demo organization/project and Development/Staging environments in Flagsmith, then connect its Organization API key from FlagForge Integrations. Follow [`docs/FLAGSMITH_SETUP.md`](docs/FLAGSMITH_SETUP.md) for the live sync walkthrough.

The Compose core includes the API, worker, PostgreSQL, Redis, and official Flagsmith services with its separate PostgreSQL, migration job, and task processor. The Next.js frontend is in the `dashboard` profile; OpenTelemetry Collector and the demo app are in the `observability` profile. Flagsmith image `v2.295.2` is pinned by tag and verified OCI digest. Host Redis maps to port 6380 to avoid a common existing Redis port conflict; containers use service DNS. Exact memory use depends on image state and workload; the previous full run approached the Docker VM's 3.58 GB limit, so start only the needed profile on an 8 GB machine.

On a small Docker VM, the official Flagsmith API's default Gunicorn process count can exhaust memory. This Compose setup uses the documented `GUNICORN_WORKERS` setting through `FLAGSMITH_GUNICORN_WORKERS` (default `1`); increase it only when the host has capacity. If Flagsmith workers are killed or requests time out, check Docker Desktop's VM memory before raising the worker count.

Check services with `./scripts/health-check.ps1 -Profile Core|Dashboard|Observability|Full`. Stop only this project while preserving its data with `./scripts/stop.ps1`. Restart with the same Compose profile used at startup. These scripts do not remove volumes or stop unrelated Compose projects.

## Tests

```powershell
$env:PYTHONPATH = "backend"
python -m pip install -r backend/requirements.txt
python -m pytest backend/tests/ -v

cd frontend
npm ci
npx tsc --noEmit
npm run build

# Headed Chromium end-to-end workflow (Docker stack must be running)
npm run test:e2e -- --headed
```

For the containerized backend suite (recommended when Docker is running):

```powershell
docker compose run --rm --no-deps --build api python -m pytest tests/ -v
```

The worker runs Redis Streams jobs for Flagsmith sync and repository scans. Demo-app OTLP metrics flow through the Collector into the authenticated FlagForge telemetry store and Risk Engine; this is demo traffic, not customer telemetry. Chaos Lab remains a synthetic, non-mutating simulation. A signed local Flagsmith webhook and Staging-only flag update/restore were live-verified in earlier QA, but fresh provider authentication and synchronization were not reverified in the latest run. FlagForge's GitHub cleanup PR workflow is implemented and mock-tested; the existing repository draft PR is a separate publication flow. Remote rollback remains disabled because race-safe conditional writes have not been established. See the [end-to-end test report](docs/END_TO_END_TEST_REPORT.md), [known limitations](docs/KNOWN_LIMITATIONS.md), [installation verification](docs/INSTALLATION_VERIFICATION_REPORT.md), [security review](docs/SECURITY_REVIEW.md) and [competition readiness report](docs/FINAL_COMPETITION_READINESS_REPORT.md) for evidence and scope.

## Companion CLI

The [FlagForge CLI package](cli/README.md) delegates provider operations to the official Flagsmith CLI and adds a read-only local Python/JavaScript/TypeScript scanner. Install the upstream Flagsmith CLI by its official instructions, then install the companion with `python -m pip install -e ./cli`. The upstream CLI has no documented plugin API; FlagForge is a companion wrapper, not a plugin or fork.

```powershell
flagforge --help
flagforge init --api-url http://localhost:8081
flagforge doctor
flagforge scan .
```

Scanning, read-only provider reads, environment diff, and cleanup preview are implemented in the CLI. PR creation requires the reviewed dashboard workflow; sync is dry-run-only. See its README for command coverage and safety limits.

## Documentation

- [Flagsmith setup](docs/FLAGSMITH_SETUP.md)
- [Docker setup](docs/DOCKER_SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Integrations](docs/INTEGRATIONS.md)
- [Security](docs/SECURITY.md)
- [Competition readiness report](docs/FINAL_COMPETITION_READINESS_REPORT.md)
- [Official Flagsmith Docker guide](https://docs.flagsmith.com/deployment-self-hosting/hosting-guides/docker)
