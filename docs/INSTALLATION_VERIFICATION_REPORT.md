# Installation Verification Report

**Date:** 2026-11-26
**Environment:** Existing Windows host with Docker Desktop and the FlagForge repository checkout. A second physical machine was not available.

## Documented setup audit

- `setup.ps1` creates `.env` only if it does not exist, generates local secrets without displaying them, validates Compose, builds and starts the deployment, and checks health.
- `.env.example` provides local configuration. Existing `.env` was preserved and never read back into QA output.
- The combined Compose configuration includes FlagForge and official Flagsmith services, independent PostgreSQL databases, migration jobs, Redis worker, collector and demo app.
- `docker compose config --quiet` passes. Docker volumes were retained throughout this verification.

## Fresh-checkout status

An isolated clean checkout is pending final commit of the current changes. A second-machine installation is not available and cannot be claimed. This report will be updated with the isolated checkout result after setup and browser smoke checks.

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
- Compose service recreation, migration revision and health checks are still being completed for this revision.
