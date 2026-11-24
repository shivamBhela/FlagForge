---
phase: 1
plan: 1
wave: 1
gap_closure: false
---

# Plan 1.1: Monorepo Foundation, Backend Core & Dev Setup

## Objective
Establish the foundational monorepo structure, FastAPI application with versioned REST API, Next.js dark-themed frontend shell with navigation, root `docker-compose.yml`, `.env.example`, and verified `/health` endpoints.

## Context
Load these files for context:
- .gsd/SPEC.md
- .gsd/REQUIREMENTS.md
- FLAGFORGE_FULL_BUILD_PROMPT.md
- README_SELF_HOSTED.md

## Tasks

<task type="auto">
  <name>Scaffold Backend & Health Endpoint</name>
  <files>
    backend/requirements.txt
    backend/Dockerfile
    backend/app/main.py
    backend/app/core/config.py
    backend/app/api/v1/router.py
    backend/app/api/v1/endpoints/health.py
    backend/tests/test_health.py
  </files>
  <action>
    Create FastAPI backend structure with Pydantic settings, CORS middleware, versioned /api/v1 router, /health and /api/v1/health endpoints returning JSON status, database/redis checks, and pytest suite.
    AVOID: Hardcoded secrets or blocking sync calls.
    USE: Async endpoints, Pydantic v2 settings, and clean status envelopes.
  </action>
  <verify>
    python -m pytest backend/tests/test_health.py
  </verify>
  <done>
    Backend health endpoint returns 200 OK and pytest passes.
  </done>
</task>

<task type="auto">
  <name>Scaffold Frontend Shell & Navigation</name>
  <files>
    frontend/package.json
    frontend/tsconfig.json
    frontend/tailwind.config.ts
    frontend/postcss.config.js
    frontend/Dockerfile
    frontend/src/app/layout.tsx
    frontend/src/app/page.tsx
    frontend/src/app/globals.css
    frontend/src/components/Sidebar.tsx
    frontend/src/components/Header.tsx
  </files>
  <action>
    Create Next.js 14 frontend structure with dark theme styling, Tailwind CSS, Lucide icons, responsive sidebar with 12 specified navigation sections (Overview, Projects, Code Scanner, Dependency Map, Chaos Lab, Live Monitor, Release Guardian, Incidents, Cleanup Studio, Integrations, Policies, Settings), and dashboard overview page.
    AVOID: Light theme flash or missing responsive layout.
    USE: Dark developer-centric UI with proper semantic hierarchy.
  </action>
  <verify>
    Test file structures and build readiness.
  </verify>
  <done>
    Frontend shell renders clean dark layout with all navigation links.
  </done>
</task>

<task type="auto">
  <name>Docker Compose & Environment Setup</name>
  <files>
    docker-compose.yml
    .env.example
  </files>
  <action>
    Create root docker-compose.yml with services (api, web, postgres, redis, otel-collector, demo-app) and healthchecks. Create comprehensive .env.example with documented configuration.
    AVOID: Exposing secrets or insecure production defaults.
    USE: Named volumes, network isolation, and health dependencies.
  </action>
  <verify>
    Validate docker-compose.yml configuration syntax.
  </verify>
  <done>
    docker-compose config validates without errors.
  </done>
</task>

## Must-Haves
After all tasks complete, verify:
- [ ] Backend /health returns JSON with status ok
- [ ] Frontend shell files present and valid
- [ ] docker-compose.yml and .env.example are complete
