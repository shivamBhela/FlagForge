# FlagForge — Feature-Release Intelligence & Safety Platform

FlagForge is a production-minded, developer-friendly feature-release intelligence and reliability platform built around a real **Flagsmith** integration.

It connects source-code intelligence, feature-flag management, relational dependency analysis, controlled release simulation, OpenTelemetry runtime observability, and policy-governed automated recovery.

---

## Architecture Overview

```
                                      ┌─────────────────────────────────┐
                                      │        Next.js Dashboard        │
                                      │  (Overview, Graph, Chaos, etc.) │
                                      └────────────────┬────────────────┘
                                                       │ REST / JSON
                                                       ▼
┌──────────────────────┐              ┌─────────────────────────────────┐
│   Flagsmith Remote   │◄────────────►│       FastAPI Core API          │
│   (Cloud / Cluster)  │  HTTPS       │  (Auth, Scans, Risk, Guardian)  │
└──────────────────────┘              └────┬───────────┬───────────┬────┘
                                           │           │           │
                     ┌─────────────────────┘           │           └────────────────────┐
                     ▼                                 ▼                                ▼
       ┌───────────────────────────┐     ┌───────────────────────────┐    ┌───────────────────────────┐
       │   PostgreSQL 16 Storage   │     │    Redis Distributed      │    │  OpenTelemetry Collector  │
       │ (Multi-tenant, Migrations)│     │  (Locks, Celery / Queue)  │    │     (:4317 / :4318)       │
       └───────────────────────────┘     └───────────────────────────┘    └───────────────────────────┘
```

---

## Core Product Capabilities

1. **Flagsmith Integration & Synchronization**:
   - Compatible with Flagsmith Cloud (`https://edge.api.flagsmith.com/api/v1`) and self-hosted instances.
   - 256-bit Fernet credential encryption at rest. Never leaks tokens to frontend or logs.
   - SSRF protection strictly blocking loopbacks and cloud metadata endpoints (`169.254.169.254`).
   - Idempotent database synchronization with change diff tracking (`records_created`, `records_updated`, `records_unchanged`).
   - Secure HMAC-SHA256 webhook receiver for real-time reconciliation.

2. **Code Intelligence & AST Scanner (`/scanner`)**:
   - Python AST visitor and TypeScript/JavaScript regex/lexer engine detecting feature flag calls.
   - Symbol/scope identification, confidence scoring, and evidence snippet capture.
   - Matches detected flag references against the authoritative Flagsmith registry.

3. **Dependency Graph Engine (`/dependencies`)**:
   - Multi-tier relationship mapping (Flag ➔ Component ➔ Service ➔ API).
   - Inferred, explicit, and manual edges with confidence scoring.
   - Real-time downstream **Blast Radius** impact calculation (0–100 scale).

4. **Chaos Lab Sandbox (`/chaos`)**:
   - Safe simulation of flag failures exclusively in staging environments.
   - Captures pre-change snapshot, applies scenario load, and enforces **guaranteed restoration** with read-after-write verification.

5. **Runtime Observability & Live Monitor (`/monitor`)**:
   - Ingests traces and metrics attributed to feature flags via OpenTelemetry.
   - Computes request rates, error anomalies, and p50/p95/p99 latency percentiles over 5-minute rolling windows.

6. **Deterministic Risk Engine & Release Guardian (`/guardian`, `/policies`)**:
   - Deterministic mathematical risk scoring:
     $$\text{Risk} = 0.30 \times \text{DepImpact} + 0.25 \times \text{ErrorAnomaly} + 0.20 \times \text{LatencyAnomaly} + 0.15 \times \text{Criticality} + 0.10 \times \text{Velocity}$$
   - Configurable risk bands: Low (0–29), Moderate (30–49), High (50–74), Critical (75–100).
   - Policy-driven automated rollback with pre-condition safety checks, distributed locks, and state verification.

7. **Incident Response & Hybrid Explanation (`/incidents`)**:
   - Post-mortem audit trail, verified rollback records, and transparent root-cause explanations with a deterministic NO-AI fallback.

8. **Cleanup Studio (`/cleanup`)**:
   - Stale/dead flag identification and unified diff patch preview generator for technical debt elimination.

---

## Quick Start (Development)

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 2. Backend Setup
```powershell
# Set up environment
cp .env.example .env

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Running Tests
```powershell
# Run backend pytest suite (15/15 tests)
$env:PYTHONPATH="backend"
python -m pytest backend/tests/ -v

# Run frontend typecheck and build
cd frontend
npx tsc --noEmit
npm run build
```

---

## Deployment Documentation
- For self-hosted on-premises deployment: [`README_SELF_HOSTED.md`](file:///c:/Users/unbel/Downloads/FlagForge_Architecture_Package/README_SELF_HOSTED.md)
- For cloud infrastructure deployment: [`README_CLOUD.md`](file:///c:/Users/unbel/Downloads/FlagForge_Architecture_Package/README_CLOUD.md)
