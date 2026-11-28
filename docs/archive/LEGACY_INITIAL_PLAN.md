> **Archived historical plan.** This initial plan predates the implemented FastAPI/Next.js/Docker Compose architecture. It is retained for project history and is not a current implementation guide.
---
phase: 1
plan: 1
wave: 1
gap_closure: false
depends_on: []
files_modified:
  - package.json
  - pnpm-workspace.yaml
  - turbo.json
  - .gitignore
  - .dockerignore
  - .env.example
  - docker-compose.yml
  - otel-collector-config.yaml
  - apps/api/package.json
  - apps/api/Dockerfile
  - apps/api/src/index.ts
  - apps/api/src/routes/health.ts
  - apps/web/package.json
  - apps/web/Dockerfile
  - apps/worker/package.json
  - apps/worker/Dockerfile
  - apps/demo-app/package.json
  - apps/demo-app/Dockerfile
  - apps/demo-app/src/index.ts
  - packages/shared/package.json
  - setup.sh
  - setup.ps1
autonomous: true
user_setup: []

must_haves:
  truths:
    - "FlagForge monorepo is scaffolded with modular packages and workspace orchestration"
    - "Docker Compose orchestrates all 7 services (web, api, worker, postgres, redis, otel-collector, demo-app) with health checks"
    - "API exposes a health-check endpoint (/healthz) that tests Postgres and Redis connectivity"
    - "One-command setup script validates dependencies, boots the stack, and verifies service readiness"
  artifacts:
    - "package.json"
    - "docker-compose.yml"
    - "otel-collector-config.yaml"
    - "apps/api/src/routes/health.ts"
    - "setup.sh"
    - "setup.ps1"
  key_links:
    - "API health route queries PostgreSQL and Redis connectivity"
    - "Docker Compose provisions shared network connecting all 7 services"
    - "Setup script runs Docker Compose and polls API /healthz"
---

# Plan 1.1: Monorepo Scaffolding, Multi-Service Docker Compose, Health Checks, and Setup Automation

## Objective
Establish the foundational infrastructure for the FlagForge feature-flagging platform. This plan scaffolds the monorepo workspace (`web`, `api`, `worker`, `demo-app`, and `packages/shared`), configures a unified multi-service `docker-compose.yml` orchestrating all 7 required services (`web`, `api`, `worker`, `postgres`, `redis`, `otel-collector`, `demo-app`), implements deep dependency-aware health checks on the API service, and provides a cross-platform one-command setup script (`setup.sh` / `setup.ps1`) for rapid local developer onboarding.

## Context
Load these files for context:
- .gsd/SPEC.md
- .gsd/ROADMAP.md
- .gsd/STATE.md

## Tasks

<task type="auto" effort="medium">
  <name>Scaffold Monorepo Architecture and Workspace Configuration</name>
  <files>
    package.json
    pnpm-workspace.yaml
    turbo.json
    .gitignore
    .dockerignore
    .env.example
    apps/web/package.json
    apps/api/package.json
    apps/worker/package.json
    apps/demo-app/package.json
    packages/shared/package.json
  </files>
  <action>
    Configure the root monorepo architecture and package boundaries using pnpm workspaces and Turborepo:
    
    Steps:
    1. Create root `package.json` declaring workspace tooling, scripts (`build`, `dev`, `lint`, `test`, `docker:up`, `docker:down`, `clean`), and package manager (`pnpm@9.x` / Node >= 20).
    2. Create `pnpm-workspace.yaml` defining package locations:
       - `apps/*`
       - `packages/*`
    3. Create `turbo.json` defining execution pipelines:
       - `build`: depends on `^build`, outputs `["dist/**", ".next/**"]`
       - `dev`: cache `false`, persistent `true`
       - `lint`: depends on `^lint`
       - `test`: depends on `build`
       - Pass required environment variables: `NODE_ENV`, `DATABASE_URL`, `REDIS_URL`, `PORT`, `OTEL_EXPORTER_OTLP_ENDPOINT`.
    4. Create `.gitignore` and `.dockerignore` ignoring `node_modules`, `dist`, `.turbo`, `.env`, coverage reports, and logs.
    5. Create `.env.example` documenting all configuration keys:
       - App ports: `PORT_WEB=3000`, `PORT_API=4000`, `PORT_DEMO=8080`
       - Database: `POSTGRES_USER=flagforge`, `POSTGRES_PASSWORD=flagforge_dev_secret`, `POSTGRES_DB=flagforge`, `POSTGRES_PORT=5432`
       - Connection URL: `DATABASE_URL=postgresql://flagforge:flagforge_dev_secret@postgres:5432/flagforge?schema=public`
       - Redis: `REDIS_HOST=redis`, `REDIS_PORT=6379`, `REDIS_URL=redis://redis:6379`
       - OpenTelemetry: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318`, `OTEL_SERVICE_NAME=flagforge`
    6. Scaffold stub package manifests:
       - `apps/web/package.json` (Next.js dashboard frontend)
       - `apps/api/package.json` (Core REST/gRPC API engine)
       - `apps/worker/package.json` (Background evaluation and event processor)
       - `apps/demo-app/package.json` (Reference feature flag consumer application)
       - `packages/shared/package.json` (Shared domain types and utilities)

    AVOID: Hoisting service-specific dependencies (such as Next.js or pg drivers) to the root `package.json`. Keep root manifests focused strictly on orchestrator tooling and shared dev tools.
    USE: Explicit `workspace:*` dependency declarations for inter-package dependencies to ensure lockfile consistency and local package resolution.
  </action>
  <verify>
    node -e "const fs = require('fs'); const files = ['package.json', 'pnpm-workspace.yaml', 'turbo.json', '.gitignore', '.dockerignore', '.env.example', 'apps/web/package.json', 'apps/api/package.json', 'apps/worker/package.json', 'apps/demo-app/package.json', 'packages/shared/package.json']; files.forEach(f => { if (!fs.existsSync(f)) throw new Error('Missing file: ' + f); }); JSON.parse(fs.readFileSync('package.json', 'utf8')); JSON.parse(fs.readFileSync('turbo.json', 'utf8')); console.log('Monorepo manifest and configuration validation passed.');"
  </verify>
  <done>
    Root monorepo files and all 5 package manifests exist, pass JSON and YAML syntax validation, and Turborepo pipeline is configured for monorepo tasks.
  </done>
</task>

<task type="auto" effort="medium">
  <name>Configure Multi-Service Docker Compose Infrastructure and OpenTelemetry</name>
  <files>
    docker-compose.yml
    otel-collector-config.yaml
    apps/api/Dockerfile
    apps/web/Dockerfile
    apps/worker/Dockerfile
    apps/demo-app/Dockerfile
  </files>
  <action>
    Construct the unified container architecture orchestrating all 7 services in `docker-compose.yml` with healthchecks, dependency topologies, and OpenTelemetry instrumentation:

    Steps:
    1. Create `otel-collector-config.yaml`:
       - Receivers: `otlp` with `grpc` (`0.0.0.0:4317`) and `http` (`0.0.0.0:4318`) endpoints.
       - Processors: `batch` (send_batch_size: 1024, timeout: 1s), `memory_limiter` (check_interval: 1s, limit_percentage: 75).
       - Exporters: `logging` (or `debug` with detailed verbosity) and `prometheus` or local collector file pipeline.
       - Service Pipelines: configure `traces`, `metrics`, and `logs` pipelines routing through `batch` processor to exporters.
    2. Create production-ready multi-stage Dockerfiles for application services:
       - `apps/api/Dockerfile`: Node.js alpine multi-stage build, exposes 4000, includes container healthcheck via `wget --no-verbose --tries=1 --spider http://localhost:4000/healthz || exit 1`.
       - `apps/web/Dockerfile`: Next.js production build, exposes 3000, healthcheck verifying port 3000 readiness.
       - `apps/worker/Dockerfile`: Node.js alpine background worker daemon.
       - `apps/demo-app/Dockerfile`: Multi-stage image exposing 8080, healthcheck via `wget --no-verbose --tries=1 --spider http://localhost:8080/healthz || exit 1`.
    3. Create `docker-compose.yml` orchestrating all 7 services on a shared `flagforge-net` bridge network:
       - `postgres`: image `postgres:16-alpine`, volumes `postgres_data:/var/lib/postgresql/data`, healthcheck `test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]`, interval 5s, timeout 5s, retries 5.
       - `redis`: image `redis:7-alpine`, volumes `redis_data:/data`, healthcheck `test: ["CMD", "redis-cli", "ping"]`, interval 5s, timeout 5s, retries 5.
       - `otel-collector`: image `otel/opentelemetry-collector-contrib:0.95.0`, volumes `./otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml`, ports `4317:4317`, `4318:4318`, `8888:8888`.
       - `api`: build context `.`, dockerfile `apps/api/Dockerfile`, ports `4000:4000`, env_file `.env`, depends_on `postgres` (condition: service_healthy), `redis` (condition: service_healthy), `otel-collector` (condition: service_started).
       - `web`: build context `.`, dockerfile `apps/web/Dockerfile`, ports `3000:3000`, env_file `.env`, depends_on `api` (condition: service_healthy).
       - `worker`: build context `.`, dockerfile `apps/worker/Dockerfile`, env_file `.env`, depends_on `postgres` (condition: service_healthy), `redis` (condition: service_healthy), `api` (condition: service_healthy).
       - `demo-app`: build context `.`, dockerfile `apps/demo-app/Dockerfile`, ports `8080:8080`, env_file `.env`, depends_on `api` (condition: service_healthy), `otel-collector` (condition: service_started).

    AVOID: Unpinned floating container tags and missing healthchecks. Without `condition: service_healthy`, dependent services crash during container boot due to database cold start latency.
    USE: Named volumes (`postgres_data`, `redis_data`) to persist state across container recreation, and custom bridge network `flagforge-net` for deterministic internal service discovery.
  </action>
  <verify>
    docker compose config --services | grep -E "^(web|api|worker|postgres|redis|otel-collector|demo-app)$" | wc -l | grep -q "^7$" && echo "All 7 Docker Compose services verified."
  </verify>
  <done>
    `docker-compose.yml` successfully validates via `docker compose config`; all 7 services (`web`, `api`, `worker`, `postgres`, `redis`, `otel-collector`, `demo-app`) are defined with complete healthchecks, environment variables, network bindings, and multi-stage Dockerfiles.
  </done>
</task>

<task type="auto" effort="medium">
  <name>Implement Health-Check Endpoints, Service Wiring, and One-Command Setup Script</name>
  <files>
    apps/api/src/routes/health.ts
    apps/api/src/index.ts
    apps/demo-app/src/index.ts
    setup.sh
    setup.ps1
  </files>
  <action>
    Implement deep dependency-aware health check endpoints on the API and demo services, and build executable, cross-platform setup automation scripts:

    Steps:
    1. Implement API health route in `apps/api/src/routes/health.ts` and mount in `apps/api/src/index.ts`:
       - Route: `GET /healthz` (with `GET /health` alias).
       - Deep health verification logic:
         - Query PostgreSQL using `SELECT 1;` with a 2-second timeout.
         - Ping Redis using `redisClient.ping()` with a 2-second timeout.
       - Response format (HTTP 200 on all healthy, HTTP 503 if any critical dependency is down):
         ```json
         {
           "status": "healthy",
           "timestamp": "2026-11-24T12:00:00.000Z",
           "uptime": 45.2,
           "version": "0.1.0",
           "dependencies": {
             "postgres": { "status": "up", "latency_ms": 2.1 },
             "redis": { "status": "up", "latency_ms": 0.8 },
             "otelCollector": { "status": "configured", "endpoint": "http://otel-collector:4318" }
           }
         }
         ```
    2. Implement demo application health check in `apps/demo-app/src/index.ts`:
       - Route `GET /healthz` returning application status, FlagForge API reachability, and OpenTelemetry tracer status.
    3. Create POSIX bash script `setup.sh`:
       - Make executable (`chmod +x setup.sh`).
       - Step 1: Pre-flight dependency check verifying `docker` and `docker compose` are installed and Docker daemon is accessible.
       - Step 2: Environment initialization — if `.env` does not exist, copy `.env.example` to `.env` and inform user.
       - Step 3: Run `docker compose down -v` (optional clean flag) and `docker compose build --parallel`.
       - Step 4: Boot stack via `docker compose up -d`.
       - Step 5: Implement health polling loop against `http://localhost:4000/healthz`: poll every 2 seconds for up to 60 seconds until HTTP 200 and `"status":"healthy"` is returned.
       - Step 6: Print formatted summary banner with service access URLs:
         - Web UI: http://localhost:3000
         - API Engine: http://localhost:4000 (Health: http://localhost:4000/healthz)
         - Demo App: http://localhost:8080 (Health: http://localhost:8080/healthz)
         - OpenTelemetry Collector: http://localhost:4318
    4. Create PowerShell equivalent `setup.ps1` for Windows environments implementing the same pre-flight validations, `.env` copy, `docker compose up -d`, and `Invoke-RestMethod` polling loop.

    AVOID: Shallow health checks that return HTTP 200 without validating database and cache sockets, which leads to false positives during orchestrator startup.
    USE: Set `-e` / `set -euo pipefail` in `setup.sh` and `$ErrorActionPreference = "Stop"` in `setup.ps1` to ensure immediate, safe failure on unhandled errors.
  </action>
  <verify>
    bash -n setup.sh && powershell -Command "if (Test-Path setup.ps1) { Write-Output 'setup.ps1 exists' }" && node -e "const fs = require('fs'); const health = fs.readFileSync('apps/api/src/routes/health.ts', 'utf8'); if (!health.includes('/healthz') || !health.includes('postgres') || !health.includes('redis')) throw new Error('Health check missing required checks'); console.log('Health check and setup scripts verified successfully.');"
  </verify>
  <done>
    `apps/api/src/routes/health.ts` implements deep `/healthz` verifying Postgres and Redis; `setup.sh` and `setup.ps1` pass syntax verification and implement prerequisite checking, `.env` provisioning, container startup, and health polling.
  </done>
</task>

## Must-Haves
After all tasks complete, verify:
- [ ] Monorepo workspace is configured with Turborepo and pnpm workspaces
- [ ] `docker-compose.yml` configures all 7 services (`web`, `api`, `worker`, `postgres`, `redis`, `otel-collector`, `demo-app`) with healthy dependency conditions
- [ ] API service exposes deep `/healthz` endpoint validating PostgreSQL and Redis connections
- [ ] `setup.sh` and `setup.ps1` provide one-command environment initialization and readiness verification

## Success Criteria
- [ ] All 3 tasks verified passing via automated verification commands
- [ ] All 7 docker services validated via `docker compose config`
- [ ] Deep health check endpoint returns 200 OK with downstream dependency status
- [ ] One-command setup script runs without manual intervention
