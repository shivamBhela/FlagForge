<div align="center">
⚒️ FlagForge
Feature-flag release intelligence, risk analysis & safety workflows
Know where a flag is used. Understand what it can affect. Make safer release decisions.

<p> <a href="https://github.com/shivamBhela/FlagForge"><img src="https://img.shields.io/badge/Project-FlagForge-2563eb?style=for-the-badge" alt="FlagForge project"></a> <a href="https://github.com/Flagsmith/flagsmith"><img src="https://img.shields.io/badge/Provider-Flagsmith-16a34a?style=for-the-badge" alt="Flagsmith provider"></a> <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11 or newer"> <img src="https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js" alt="Next.js 16"> <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose"> </p>
Explore the repository · Architecture · Setup guide · Known limitations

</div>
[!IMPORTANT]
Project status — local development and competition-demo prototype. FlagForge is not production-ready and must not be exposed directly to the public internet. The latest recorded QA run passed the core application checks, but a fresh Flagsmith Management API connection was not verified in that run. Read Current verification & limitations before evaluating the project.

✨ What is FlagForge?
Feature flags help teams release functionality gradually, run controlled experiments and switch features without redeploying an application. As a codebase grows, however, flag-related knowledge can become scattered across source files, services, environments and runtime dashboards.

FlagForge brings that information into one release-intelligence workflow. It adds code scanning, dependency visibility, runtime observations, deterministic risk assessment, simulation and human-reviewed cleanup around the official Flagsmith platform.

Flagsmith remains the feature-flag provider and source of truth. FlagForge does not replace it or evaluate flags on its behalf.

🧭 At a glance
<table> <tr> <td width="33%" valign="top"><strong>🔎 Discover</strong><br>Find feature-flag references in Python, JavaScript and TypeScript code.</td> <td width="33%" valign="top"><strong>🕸️ Understand</strong><br>Explore inferred flag-to-component-to-service relationships and estimated blast radius.</td> <td width="33%" valign="top"><strong>📈 Observe</strong><br>Review request, error and latency signals when telemetry is available.</td> </tr> <tr> <td width="33%" valign="top"><strong>🛡️ Assess</strong><br>Calculate an explainable release-risk score with evidence and confidence context.</td> <td width="33%" valign="top"><strong>🧪 Simulate</strong><br>Demonstrate Staging risk scenarios without provider mutation or load generation.</td> <td width="33%" valign="top"><strong>🧹 Review</strong><br>Inspect potential stale references and prepare a human-reviewed cleanup change.</td> </tr> </table>
📚 Table of contents
What is FlagForge?
At a glance
Core modules
How it works
Risk scoring
Architecture
Technology stack
Getting started
Connect Flagsmith
Companion CLI
Testing
Current verification & limitations
Repository structure
Security
Documentation
🧩 Core modules
Module	What it does	Why it matters
Dashboard	Summarizes organizations, projects, environments, flags, scans and release intelligence.	Gives teams one place to review feature-flag activity.
Flagsmith Integration	Connects to a self-hosted Flagsmith instance through its Management API and imports project, environment, feature and environment-state data.	Keeps Flagsmith as the provider source of truth while making its metadata available to FlagForge.
Code Scanner	Finds supported static flag references in Python, JavaScript and TypeScript; records file, line, evidence and confidence.	Helps developers locate where flags are used.
Dependency Intelligence	Builds an inferred flag → component → service graph and estimates downstream blast radius.	Helps reviewers understand potential impact before changing a flag.
Runtime Monitor	Accepts authenticated OpenTelemetry data and presents request, error and latency observations when available.	Adds runtime context to release decisions.
Release Guardian	Calculates a deterministic 0–100 risk score and recommends rollout review actions.	Makes risk factors and missing evidence visible.
Chaos Lab	Runs labelled synthetic Staging scenarios.	Demonstrates risk behaviour without sending load or changing Flagsmith.
Incident / Risk Views	Shows assessments and their contributing evidence.	Makes it easier to understand why a release needs attention.
Cleanup Studio	Reviews possible stale references and prepares a human-reviewed cleanup change.	Supports safer code cleanup; external GitHub PR creation needs credentials.
Companion CLI	Adds local scanning, read-only flag inspection and environment comparison helpers alongside the official Flagsmith CLI.	Makes selected checks available from a developer terminal.
🔄 How it works
A typical workflow follows these steps:

Manage flags in Flagsmith. Create a project and environments such as Development and Staging. Flagsmith remains the provider and source of truth.
Connect FlagForge. An organization-level Management API key is entered in the Integrations screen. The backend uses it to discover projects, environments, features and environment states. The credential is stored encrypted server-side and is not returned to the browser.
Synchronize metadata. FlagForge stores tenant-scoped copies of provider metadata in its own database. Sync jobs can be processed by the Redis Streams worker. FlagForge does not access or share Flagsmith's SQL database.
Scan source code. The scanner records supported flag references with file paths, line numbers, evidence snippets and parser confidence. References can be matched against known flags or marked unresolved.
Infer dependencies. The dependency engine connects flags to source components and inferred service groupings. This graph supports blast-radius estimation; it is not a complete runtime dependency map.
Ingest runtime observations. The demo application can send OpenTelemetry data through the Collector to an authenticated FlagForge ingestion endpoint. The backend stores tenant-attributed request, error and latency observations.
Assess release risk. The Risk Engine combines dependency impact, error anomaly, latency anomaly, change criticality and rollout velocity. Release Guardian presents the score, evidence and recommended action for human review.
Simulate or review cleanup. Chaos Lab demonstrates synthetic Staging scenarios. Cleanup Studio supports human-reviewed change preparation. Neither silently merges code nor performs an automatic production rollback.
📊 Risk scoring
The Risk Engine uses a weighted, deterministic score bounded from 0 to 100:

Risk score =
    0.30 × dependency impact
  + 0.25 × error anomaly
  + 0.20 × latency anomaly
  + 0.15 × change criticality
  + 0.10 × rollout velocity
Score	Risk band	Recommended action
0–29.99	🟢 Low	ALLOW_ROLLOUT
30–49.99	🟡 Moderate	PROCEED_WITH_CANARY
50–74.99	🟠 High	MANUAL_APPROVAL_REQUIRED
75–100	🔴 Critical	MANUAL_APPROVAL_REQUIRED
The weights and policy thresholds are policy-backed. Missing telemetry is not treated as healthy telemetry. When minimum sample or histogram evidence is unavailable, the engine uses conservative anomaly inputs and forces manual approval. Scores are advisory decision support, not proof that a release is safe.

Rollback safety: Remote rollback is intentionally disabled. A provider-side conditional-write/concurrency guarantee has not been established, so an automated restore could overwrite a newer change made by another actor. The rollback endpoint returns HTTP 501 without mutating provider state.

🏗️ Architecture
Developer / reviewer
FlagForge Next.js dashboard
FlagForge FastAPI
FlagForge PostgreSQL
Redis Streams
FlagForge worker
Official Flagsmith service
Separate Flagsmith PostgreSQL
Flagsmith task processor
Demo application
OpenTelemetry Collector
Management API
OTLP / HTTP
Authenticated telemetry
Service boundaries
FlagForge PostgreSQL stores FlagForge users, organizations, integrations, synchronized snapshots, scans, dependencies, risk assessments and telemetry records.
Flagsmith PostgreSQL stores the official Flagsmith application data. It is separate from FlagForge's database.
Redis supports FlagForge streams, job state, locks and cache.
Flagsmith Management API is the supported integration boundary. FlagForge does not read or write the provider's database directly.
OpenTelemetry Collector forwards demo workload observations to FlagForge's authenticated ingestion endpoint.
Within Docker Compose, services communicate through their internal service names. The setup script prints the browser-facing addresses for the selected local profile; those machine-specific addresses are deliberately not hard-coded in this README.

🧰 Technology stack
Layer	Technology
Frontend	Next.js 16, React 19, TypeScript, Tailwind CSS
Backend API	Python 3.11+, FastAPI, Pydantic v2
Persistence / ORM	PostgreSQL 16, SQLAlchemy 2.x async, Alembic
Cache and jobs	Redis 7, Redis Streams, worker service
Feature-flag provider	Official self-hosted Flagsmith v2.295.2
Observability	OpenTelemetry SDK / Collector, OTLP over HTTP
Packaging	Dockerfiles and Docker Compose profiles
Companion CLI	Python 3.11+ wrapper around the official Flagsmith CLI and a local source scanner
🚀 Getting started
Prerequisites
Windows x64 with Docker Desktop using the Linux container engine.
Docker Compose v2.
PowerShell 7 is recommended for the provided setup and health-check scripts.
At least 4 GB of memory available to Docker for the Dashboard profile. The Full profile starts additional services and needs more headroom; on a memory-constrained machine, begin with Core.
1. Clone the repository
git clone https://github.com/shivamBhela/FlagForge.git
cd FlagForge
2. Start the stack
# Start the full interactive demo: Core + Dashboard + Observability
.\setup.ps1 -Profile Full
The setup script checks Docker availability, creates .env with unique local-only secrets if it is missing, preserves an existing .env, validates Compose, starts the selected profile and runs health checks. It does not delete existing named volumes.

Available profiles
Profile	Services started	Recommended use
Core	FlagForge API, worker, PostgreSQL, Redis and official Flagsmith services	Backend and provider integration work; lowest resource use. Default profile.
Dashboard	Core + Next.js dashboard	Browser-based application walkthrough.
Observability	Core + OpenTelemetry Collector + demo app	Telemetry pipeline and demo workload checks without the dashboard.
Full	Core + Dashboard + Observability	Full interactive local demonstration.
Start a selected profile with:

.\setup.ps1 -Profile Core
.\setup.ps1 -Profile Dashboard
.\setup.ps1 -Profile Observability
.\setup.ps1 -Profile Full
To add optional services to an already-running Core stack:

# Add the web dashboard
docker compose --profile dashboard up --build -d web

# Add the Collector and demo application
docker compose --profile observability up --build -d otel-collector demo-app
3. Open the application
After startup, the setup script prints the browser-facing addresses for the services included in the selected profile. Use those generated addresses to open the FlagForge dashboard, API documentation, Flagsmith dashboard and (when enabled) the demo application. They are intentionally omitted here because they point to the machine running Docker, not to a shared hosted demo.

4. Check and stop services
# Check service health and migrations
.\scripts\health-check.ps1 -Profile Full

# Stop this project while retaining its database and Redis volumes
.\scripts\stop.ps1

# Restart with the same profile used earlier
docker compose --profile dashboard --profile observability up -d
Data safety: Do not run docker compose down -v unless you intentionally want to delete the named FlagForge, Flagsmith and Redis volumes. The provided stop script preserves persisted data and does not stop unrelated Compose projects.

🔌 Connect Flagsmith
This project runs the official self-hosted Flagsmith service alongside FlagForge for local development and demonstration.

Start the Core or Full profile.
Open the Flagsmith dashboard address printed by the setup script. On first launch, complete the initial administrator setup.
Create a dedicated demo organization and project. Add Development and Staging environments. A Production environment may be added for viewing or policy demonstrations, but do not use real production flags.
Create a disposable test flag, for example FLAGFORGE_LIVE_TEST.
In Flagsmith Organization Settings → API Access, create an Organization API key with the shortest practical expiry.
Open the FlagForge dashboard, register or sign in, select an organization and open Integrations.
Select Flagsmith Local. Use the Docker Compose Flagsmith service endpoint configured in the example environment; the default is the internal flagsmith service on port 8000 with the Management API prefix /api/v1.
Enter the Organization API key in the integration credential field, select Test Connection, save it and select Sync Now.
Confirm the provider project, environments, feature definitions and environment states appear in FlagForge.
Change only the disposable test flag in Flagsmith Development, sync again and confirm the updated state appears in FlagForge. Repeat the sync to check that duplicate snapshots are not created.
Know your Flagsmith credentials
Credential	Purpose	Where it belongs
Organization Management API key	Discover projects, environments, flags and synchronize provider data.	Enter in the FlagForge backend integration form; stored encrypted server-side.
Environment SDK key	Evaluate flags for a specific Flagsmith environment in an application.	Optional local .env value FLAGSMITH_ENVIRONMENT_KEY for the demo app only.
Dashboard login	Sign in to the Flagsmith web dashboard.	Used only for the Flagsmith dashboard login.
These credentials are not interchangeable. Never put an Organization API key or server-side SDK key in a NEXT_PUBLIC_* variable, source file, screenshot, issue or chat message.

See the detailed Flagsmith setup guide for the local walkthrough, optional webhook setup and safety boundaries.

💻 Companion CLI
The companion CLI is installed separately from the web stack. It delegates provider operations such as flag listing, inspection and environment reads to the official Flagsmith CLI. It adds local source scanning and analysis around those operations.

# Install the official Flagsmith CLI using its upstream instructions first.
# From the repository root, install the FlagForge companion:
python -m pip install -e .\cli

flagforge --help
flagforge doctor
flagforge scan .
Available command groups:

flagforge init [--api-url URL]
flagforge doctor
flagforge flags list
flagforge flags inspect NAME
flagforge flags audit
flagforge scan [PATH]
flagforge scan-repo https://github.com/OWNER/REPOSITORY
flagforge dependencies
flagforge diff SOURCE TARGET [--no-input]
flagforge sync --dry-run
flagforge risk assess --flag KEY [--environment NAME]
flagforge cleanup preview
flagforge monitor
flagforge report [--path PATH] [--format json|markdown]
flagforge github pr
CLI safety boundaries: diff is read-only; sync is dry-run only; github pr does not create a branch or pull request; and risk/cleanup commands require the appropriate authenticated application context. The upstream Flagsmith CLI is a standalone Go program and does not document a plugin API. FlagForge is a companion wrapper, not an official Flagsmith plugin or fork. See README.md for full command details.

✅ Testing
Backend
$env:PYTHONPATH = "backend"
python -m pip install -r backend/requirements.txt
python -m pytest backend/tests/ -v
Or run tests in the API image:

docker compose run --rm --no-deps --build api python -m pytest tests/ -v
Frontend
cd frontend
npm ci
npx tsc --noEmit
npm run lint
npm run build
Browser end-to-end workflow
With the Docker stack running:

cd frontend
npm run test:e2e -- --headed
Companion CLI
From the repository root:

python -m unittest discover -s cli/tests -v
See the end-to-end test report and final competition readiness report for dated evidence.

🔍 Current verification & limitations
Latest recorded QA snapshot: 28 November 2026. These results describe a local test run, not a production-readiness rating or a competition score.

Area	Latest recorded result
Docker Full profile	10 long-running services healthy; both one-shot migration jobs exited successfully.
Database	Alembic current/head at 009_encrypt_webhook_secrets; isolated backup/restore drill passed for both PostgreSQL databases.
Backend tests	46 passed.
Companion CLI tests	12 passed.
Frontend	ESLint, TypeScript and production build passed; 20 routes generated.
Dependency audit	npm audit reported 0 vulnerabilities in the recorded run.
Browser workflow	1 headed Playwright workflow passed in 19.8 seconds; exercised 18 route experiences and a 390px viewport.
Known limitations
Fresh Flagsmith connection not verified in the latest QA run. The latest browser session showed no connected Flagsmith instance and did not make a provider request. Earlier isolated local Staging synchronization and signed-webhook checks are historical evidence, not a fresh result. Reconnect with a valid Organization Management API key and repeat the live test before claiming the integration is currently connected.
GitHub integration not live-verified for the app workflow. Cleanup-to-PR is implemented and mock-tested, but no external GitHub credentials or test repository were configured for the latest QA pass. The repository's own draft PR is publication evidence, not proof that Cleanup Studio created a PR.
Telemetry shown in the demo is not customer telemetry. The latest browser session displayed zero telemetry windows. Do not interpret missing observations as healthy service behaviour.
Chaos Lab is synthetic only. It does not generate load or mutate the Flagsmith provider.
Remote rollback is disabled. The endpoint returns HTTP 501 and does not change provider state.
CLI sync is dry-run only. The CLI environment comparison uses read-only provider reads; live comparison was not run in the latest recorded CLI test suite.
Production hardening is incomplete. Public TLS/ingress, high availability, production load testing and independent security/penetration testing have not been verified. Do not expose the local Compose stack publicly.
The dated readiness and limitations documents are the source of truth for detailed evidence and updates. Re-run tests and provider checks before making claims about a later build.

🗂️ Repository structure
FlagForge/
├── backend/                 # FastAPI application, models, services, migrations and tests
│   ├── app/
│   │   ├── api/             # API dependencies and versioned routes
│   │   ├── core/            # Configuration, auth and shared infrastructure
│   │   ├── models/          # SQLAlchemy data models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Scanner, Flagsmith, risk, telemetry, cleanup, etc.
│   │   └── worker.py        # Redis Streams worker
│   └── tests/               # Backend tests
├── frontend/                # Next.js / React dashboard and browser tests
├── demo-app/                # Reference app for flag evaluation and telemetry demos
├── cli/                     # FlagForge companion CLI and CLI tests
├── docs/                    # Architecture, setup, security, test and readiness docs
├── scripts/                 # Health-check and safe stop scripts
├── docker-compose.yml       # Local multi-service deployment
├── otel-collector-config.yaml
├── setup.ps1                # Windows setup and profile launcher
├── .env.example             # Configuration template; never put real secrets here
└── README.md
🔐 Security
Use a dedicated disposable Flagsmith organization and project for local demos.
Use an Organization Management API key with minimum practical scope and expiry.
Never expose server-side keys to browser code or commit secrets.
FlagForge encrypts stored integration credentials and keeps provider calls on the backend.
Do not broaden the outbound provider host allowlist casually.
Webhook signatures are verified against the raw request body; use a separate random signing secret and test only against a QA Staging environment.
Keep the application bound to local interfaces unless a separate production deployment and security review has been completed.
Do not enable automated provider rollback without a safe concurrency/conditional-write design and new verification.
📖 Documentation
Guide	Description
Architecture
Services, data boundaries and request flows.
Docker setup & data safety
Profiles, startup, health checks, persistence and backups.
Flagsmith setup
Provider setup, credentials, sync and optional webhooks.
Integration details
Flagsmith, GitHub, OpenTelemetry and worker integration status.
Security guide
Credential handling and application security boundaries.
Security review
Recorded security checks and remaining gaps.
Known limitations
Explicitly unverified or unavailable behaviour.
End-to-end test report
Automated and browser verification evidence.
Competition readiness report
Dated local readiness assessment.
Companion CLI guide
CLI installation, commands and safety limitations.
🙏 Acknowledgements
FlagForge is built around the official open-source Flagsmith platform. Flagsmith is deployed as a separate service and remains the feature-flag provider; FlagForge is an independent companion application.

<div align="center"> <sub>Built for safer, more informed feature-flag releases.</sub> </div>
