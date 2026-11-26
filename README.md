# FlagForge

FlagForge is a feature-flag release intelligence prototype built on the official [self-hosted Flagsmith](https://github.com/Flagsmith/flagsmith) platform. Flagsmith and FlagForge have separate PostgreSQL databases and communicate through the supported Flagsmith Management API.

## Start the local demonstration

Requirements: Windows x64, Docker Desktop with Linux containers, Docker Compose v2, PowerShell 7, and at least 4 GB of memory available to Docker. Start Docker Desktop first.

```powershell
.\setup.ps1
```

If `.env` is absent, setup generates unique local secrets without displaying them. It validates Compose, builds and starts the combined stack, then checks services. Existing `.env` files are preserved.

- Flagsmith dashboard: [http://localhost:8081](http://localhost:8081)
- FlagForge dashboard: [http://localhost:3000](http://localhost:3000)
- FlagForge API docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- Demo app: [http://localhost:8080](http://localhost:8080)

Create a dedicated demo organization/project and Development/Staging environments in Flagsmith, then connect its Organization API key from FlagForge Integrations. Follow [`docs/FLAGSMITH_SETUP.md`](docs/FLAGSMITH_SETUP.md) for the live sync walkthrough.

The Compose stack includes seven FlagForge services plus the official Flagsmith application, its separate PostgreSQL, migration job, and task processor. Flagsmith image `v2.295.2` is pinned by tag and verified OCI digest. Host Redis maps to port 6380 to avoid a common existing Redis port conflict; containers use service DNS.

Check services with `./scripts/health-check.ps1`. Stop only this project while preserving its data with `./scripts/stop.ps1`. Restart with `docker compose up -d`. These scripts do not remove volumes or stop unrelated Compose projects.

## Tests

```powershell
$env:PYTHONPATH = "backend"
python -m pytest backend/tests/ -v
cd frontend
npx tsc --noEmit
npm run build
```

The worker runs Redis Streams jobs for Flagsmith sync and repository scans. Demo-app OTLP metrics flow through the Collector into the authenticated FlagForge telemetry store and Risk Engine. The local Flagsmith connection and synchronization are live-verified. Chaos Lab remains a non-mutating simulation. Native Flagsmith webhook delivery is not live-verified; GitHub PR creation and remote rollback remain disabled (HTTP 501). See the [end-to-end test report](docs/END_TO_END_TEST_REPORT.md), [known limitations](docs/KNOWN_LIMITATIONS.md) and [competition readiness report](docs/FINAL_COMPETITION_READINESS_REPORT.md) for evidence and scope.

## Documentation

- [Flagsmith setup](docs/FLAGSMITH_SETUP.md)
- [Docker setup](docs/DOCKER_SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Integrations](docs/INTEGRATIONS.md)
- [Security](docs/SECURITY.md)
- [Competition readiness report](docs/FINAL_COMPETITION_READINESS_REPORT.md)
- [Official Flagsmith Docker guide](https://docs.flagsmith.com/deployment-self-hosting/hosting-guides/docker)
