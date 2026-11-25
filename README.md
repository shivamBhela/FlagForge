# FlagForge

FlagForge is a feature flag release management prototype built with Next.js, FastAPI, SQLAlchemy/Alembic, PostgreSQL, and Redis. It includes organization/project management, a code scanner, dependency graph, risk evaluation, synthetic Chaos Lab, telemetry aggregation, Flagsmith Management API synchronization, and cleanup diff previews.

## Current verification status

This repository has been exercised locally with SQLite, mocked Flagsmith API responses, and headed Chromium. The full backend suite and frontend type check pass. Docker services and live Flagsmith connectivity were not verified in this environment: the Docker Desktop engine was unavailable and no Flagsmith credentials were configured. The worker is a placeholder, OpenTelemetry is not wired end-to-end into FlagForge, GitHub PR creation is unavailable, and remote rollback is disabled. See [`docs/FINAL_COMPETITION_READINESS_REPORT.md`](docs/FINAL_COMPETITION_READINESS_REPORT.md) for evidence and limitations.

## Local development

Prerequisites: Python 3.11+, Node.js 18+, and Docker Compose for the full PostgreSQL/Redis stack. Copy `.env.example` to `.env` and replace development secrets before using data that matters. Never use the sample values in production.

```powershell
docker compose up --build -d
docker compose ps
```

The API is at `http://localhost:8000`, the web app at `http://localhost:3000`, and the demo app at `http://localhost:8080`. The API liveness route is `/health`; `/api/v1/healthz` probes PostgreSQL and Redis and returns degraded when a required dependency is unavailable. Alembic migrations run from the backend container on startup; verify with `docker compose logs api` and `docker compose exec api alembic current`.

For host-based backend development:

```powershell
$env:PYTHONPATH = "backend"
python -m pip install -r backend/requirements.txt
python -m alembic -c backend/alembic.ini upgrade head
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

For frontend development:

```powershell
cd frontend
npm ci
npm run dev
```

## Tests and build

```powershell
$env:PYTHONPATH = "backend"
python -m pytest backend/tests/ -v
cd frontend
npx tsc --noEmit
npm run build
```

Flagsmith Cloud uses the Management API at `https://api.flagsmith.com/api/v1` with an organization Management API key. Credentials are entered through the Integrations screen and stored encrypted by the API. Live behavior depends on a reachable Flagsmith instance and valid credentials. Local/private self-hosted endpoints are blocked by SSRF protections; use a publicly routable HTTPS host.

## Implemented behavior and boundaries

- Flagsmith connection checks, paginated project/environment/feature discovery, and synchronization are implemented and covered with mocked HTTP tests. Live provider compatibility remains unverified.
- Webhook HMAC validation is a FlagForge-specific contract. Native Flagsmith webhook signature compatibility has not been verified.
- Chaos Lab only produces synthetic records; it does not change remote flags or generate load, and does not claim restoration.
- Risk evaluation requires sufficient telemetry for a favorable decision. Current telemetry ingestion accepts aggregate batches; the configured OpenTelemetry Collector is not an ingestion path into that store.
- Release Guardian remote rollback returns HTTP 501 until a provider write and read-after-write verification are implemented.
- Cleanup patch previews are local proposals. GitHub pull request creation returns HTTP 501 because no GitHub App integration is configured.
- The `worker` service currently starts a placeholder loop and consumes no jobs.

## Security notes

Keep `.env` and provider tokens out of source control and logs. Use unique production secrets, TLS at public boundaries, backups for persistent databases, and an ingress policy appropriate for your deployment. Review [README_SELF_HOSTED.md](README_SELF_HOSTED.md) and [README_CLOUD.md](README_CLOUD.md) as deployment drafts; neither is a substitute for a deployment-specific security review.
