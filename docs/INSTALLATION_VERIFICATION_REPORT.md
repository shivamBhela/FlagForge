# Installation Verification Report

**Date:** 2026-11-26
**Environment:** Existing Windows host with Docker Desktop and the FlagForge repository checkout. A second physical machine was not available.

## Documented setup audit

- `setup.ps1` creates `.env` only if it does not exist, generates local secrets without displaying them, validates Compose, builds and starts the deployment, and checks health.
- `.env.example` provides local configuration. Existing `.env` was preserved and never read back into QA output.
- The combined Compose configuration includes FlagForge and official Flagsmith services, independent PostgreSQL databases, migration jobs, Redis worker, collector and demo app.
- `docker compose config --quiet` passes. Docker volumes were retained throughout this verification.

## Fresh-checkout verification

- Cloned committed revision `acd08d4` to `C:\Users\unbel\Downloads\FlagForge_CleanInstall_QA` and ran the documented `setup.ps1` on this same Windows/Docker Desktop host.
- Set `COMPOSE_PROJECT_NAME=flagforge-clean-qa` for the isolated checkout. Setup created a fresh ignored `.env` with generated local secrets; secret values were not printed or committed.
- Docker built the API, worker, migration, demo and Next.js production images from the clone. The frontend production build generated all 20 routes and npm reported zero vulnerabilities.
- All 10 long-running services became healthy; both FlagForge and Flagsmith one-shot migrations exited 0. The documented health script passed HTTP probes for API, web, demo, Flagsmith and Collector.
- Ran the headed Chromium Playwright workflow against the fresh deployment: **1 passed (32.6s)**. It registered a disposable QA account, created an organization/project/environment, checked persistence, traversed every route, ran only the synthetic Staging scenario, checked filters, mobile width, logout/login, and observed no uncaught browser errors or HTTP 5xx responses.
- The clean checkout used Compose-scoped volumes distinct from the original project. The original named volumes were retained. The clean checkout was not a second physical machine; no cross-host installation claim is made.

## Host backend test setup

Install dependencies before running pytest from the host:

```powershell
python -m pip install -r backend/requirements.txt
$env:PYTHONPATH = "backend"
python -m pytest backend/tests/ -v
```

Or run in the same dependency image used by the project:

```powershell
docker compose run --rm --no-deps --build api python -m pytest tests/ -v
```

## Current evidence

- Backend container test suite: 35 passed.
- `npx tsc --noEmit`: passed.
- `npm run build`: passed.
- Compose service recreation, fresh-checkout migrations, browser smoke and health checks passed. Alembic head is `009_encrypt_webhook_secrets`.
