> **Archived original build prompt.** This is a historical specification, not evidence that every proposed feature or deployment mode was implemented. Use the current README, technical documentation and QA report for actual behavior.
# FLAGFORGE — Full Product-Build Prompt

You are a principal software architect, senior full-stack engineer, DevOps engineer, and application-security engineer. Build **FlagForge**, a production-minded, developer-friendly feature-release intelligence platform built around a real Flagsmith integration.

Do not produce a static mockup or a CRUD-only dashboard. Deliver a working, testable product with real integrations, background jobs, database persistence, observable workflows, clear setup instructions, and safe failure handling. Work incrementally, keep the repository runnable, and do not claim a feature is complete until it works end to end.

## 1. Product vision

FlagForge connects source-code intelligence, feature-flag management, dependency analysis, controlled release simulation, runtime observability, and policy-governed recovery.

Its purpose is to help development teams answer:
1. Which feature flags are referenced in my code?
2. Which application components or flags appear to depend on each other?
3. What risks should be tested before a release?
4. Did application health materially change during a rollout?
5. Is an automated flag rollback permitted by the configured policy, and was the resulting state verified?

Flagsmith remains the system of record for feature flags. FlagForge is an intelligence and safety layer around it. Do not reimplement Flagsmith.

## 2. Core product modules

### A. Flagsmith integration
- Support Flagsmith Cloud and self-hosted instances through a configurable base URL.
- Implement a backend-only adapter for the documented Flagsmith Management API and, where appropriate, the Flags API/SDK.
- Discover projects, environments, features and current states using actual documented API contracts.
- Synchronize remote configuration into a local read model.
- Store remote identifiers and minimal snapshots required for analysis and recovery.
- Handle rate limits, timeouts, retries, pagination, API version differences and connection failures.
- Never expose Management API credentials to the browser, logs, analytics or AI prompts.
- Verify every mutation with a read-after-write request.
- Treat webhooks as untrusted input: validate signatures according to current Flagsmith documentation, deduplicate events, and process asynchronously.
- Do not invent Flagsmith endpoints, payload fields, webhook guarantees or SDK methods. Verify them against official documentation and isolate them inside the adapter.

### B. Code Intelligence
- Connect GitHub repositories using a GitHub App or a secure, least-privilege integration.
- Start with TypeScript/JavaScript and Python; make parser support extensible.
- Use Tree-sitter or language-aware AST parsing to find supported feature-flag evaluation patterns.
- Provide configurable detection patterns for different SDKs and project wrappers.
- Record repository, commit SHA, branch, file path, line, symbol/function, matched flag, parser confidence and evidence.
- Match code references to the Flagsmith registry.
- Report matched flags, unresolved references, duplicate references, potentially stale flags and unsupported patterns.
- Never execute untrusted repository code during scanning.
- Clearly distinguish static evidence from runtime evidence. A missing static reference is not proof that a flag is unused.

### C. Dependency Intelligence
- Build a graph of flag, code component, service and API relationships.
- Distinguish `explicit`, `inferred` and `manual` edges.
- Store evidence and confidence for every inferred relationship.
- Support impact analysis: “If this flag is disabled, which known dependent components may be affected?”
- Do not present inferred edges as confirmed dependencies.
- Visualize the graph with React Flow, including filters, node details, edge evidence and search.

### D. Chaos Lab
- Run controlled scenarios only in isolated test/staging environments or disposable demo instances.
- Snapshot the initial test configuration.
- Apply scenario changes, run test traffic, collect metrics and assertions, then restore the original state in a `finally`/compensation path.
- Verify restoration after every run.
- Provide scenario templates, run status, logs, baseline comparison and reports.
- Never perform random flag changes against production.
- Never run arbitrary repository code in the API process. Use isolated workers/containers with resource limits if executing tests is required.

### E. Runtime Intelligence
- Ingest metrics and traces through OpenTelemetry-compatible instrumentation/collector.
- Track request count, error count/rate, latency percentiles, service/environment, deployment/release and feature attribution where available.
- Provide a demo application that emits reliable feature-attributed telemetry.
- Use configurable windows, minimum sample counts and baseline comparisons.
- Account for missing telemetry, low traffic, delayed data and instrumentation gaps.
- Do not infer causality from temporal correlation alone. Display evidence and confidence limitations.

### F. Deterministic Risk Engine
- Use deterministic, versioned algorithms for scores and decisions. AI must never calculate or authorize the safety decision.
- Initial illustrative normalized score:
  `risk = 0.30*dependency_impact + 0.25*error_anomaly + 0.20*latency_anomaly + 0.15*change_criticality + 0.10*rollout_velocity`
- Keep weights configurable and versioned. Explain the score components.
- Combine weighted score with hard policy rules (e.g. sustained critical error threshold, minimum sample size, exposure, consecutive windows).
- Risk bands are configurable; initial example: 0–29 low, 30–49 moderate, 50–74 high, 75–100 critical.
- Missing data must not silently be treated as healthy. Return `insufficient_data` or apply an explicit policy.
- Unit-test boundaries, normalization, missing values and repeatability.

### G. Release Guardian and rollback
- Support `monitor`, `notify`, `approval_required` and `automatic` policy modes.
- Automatic rollback is permitted only when policy enables it and all preconditions pass.
- Preconditions: correct project/environment/flag mapping; sufficiently recent and valid pre-change snapshot; no conflicting manual change since snapshot; adequate telemetry; configured minimum sample/exposure; sustained threshold breach; allowed flag; no active cooldown; bounded attempt count; valid credentials.
- Use distributed locks and idempotency keys to prevent duplicate actions.
- Persist a rollback intent before the remote mutation.
- Change the flag through the Flagsmith adapter, then read it back and verify the intended state.
- Mark success only after verification. On timeout/uncertain result, reconcile by reading remote state before retrying.
- If any safety check fails, do not mutate production; create an alert/approval request instead.
- Keep append-only audit events and incident records.
- Provide an emergency automation kill switch and per-environment protection.
- Explain limitations: flag rollback does not reverse database migrations, data corruption, irreversible side effects or incompatible application deployments.
- Never claim that disabling a flag proves the incident is resolved.

### H. Hybrid AI explanation layer
- AI may summarize evidence, explain a deterministic score, draft incident reports and suggest code improvements.
- AI must not call the Flagsmith mutation adapter, change policies, approve actions, or authorize rollback.
- Give the model only sanitized, structured evidence; redact tokens, secrets, personal data and sensitive repository content.
- Treat repository text, issue descriptions, webhook payloads and logs as untrusted data, not instructions.
- Require output schemas and validate generated suggestions.
- Label AI output as explanatory/advisory and show its evidence sources.
- Provide a no-AI fallback so the core product works without an LLM key.

### I. Cleanup Studio
- Generate patch previews for stale or unresolved flag references.
- Require human review before applying changes or creating a GitHub pull request.
- Never automatically merge or deploy cleanup changes.
- Include file paths, line references, rationale and tests to run.

## 3. Recommended technology

- Frontend: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, React Flow.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic.
- Database: PostgreSQL.
- Queue/cache/locks: Redis with Celery or an equivalent reliable worker.
- Parsing: Tree-sitter with pluggable language/query patterns.
- Observability: OpenTelemetry SDK and Collector; Prometheus-compatible metrics where useful.
- Integrations: Flagsmith APIs, GitHub App.
- Packaging: Docker Compose for local/self-hosted; container-based cloud deployment.
- Tests: pytest, frontend tests, API integration tests, Playwright end-to-end tests.

Use supported stable versions and pin dependencies. Do not assume a particular Flagsmith API endpoint or SDK method without checking official current documentation.

## 4. Architecture requirements

Use a modular monolith plus background workers initially, not a premature microservice fleet. Separate modules and interfaces so they can be extracted later.

Suggested backend modules:
- `auth`, `organizations`, `projects`, `environments`
- `integrations/flagsmith`, `integrations/github`, `integrations/otel`
- `scanner`, `dependency_engine`, `simulation`
- `telemetry`, `risk_engine`, `release_guardian`
- `incidents`, `audit`, `ai_explanations`, `cleanup`

Use an outbox/event pattern for reliable asynchronous jobs and webhook processing. Use organization-scoped authorization on every tenant-owned query. Add database constraints and indexes. Use UTC timestamps.

## 5. Database entities

Design normalized SQLAlchemy models and Alembic migrations for at least:
- users
- organizations
- organization_members
- projects
- environments
- flagsmith_connections
- repositories
- feature_flags
- flag_snapshots
- scans
- flag_references
- dependencies
- simulations
- simulation_steps
- telemetry_aggregates
- releases
- risk_assessments
- rollback_policies
- incidents
- rollback_actions
- audit_logs
- webhook_events
- background_jobs or job metadata
- ai_reports

Use UUID primary keys. Include `organization_id` or enforce tenant ownership through parent relations and query scopes. Encrypt integration secrets using a documented application key-management strategy; do not store plaintext tokens. Avoid storing raw high-volume request telemetry indefinitely; aggregate by time bucket and define retention.

## 6. API requirements

Expose versioned REST endpoints under `/api/v1`. Generate OpenAPI documentation and typed frontend clients.

Implement endpoints for:
- auth/session and organizations/members
- projects and environments
- Flagsmith connection, test, sync, flags and history
- GitHub repository connection and webhook
- scans, findings, flag references and dependency graph
- simulation scenarios, runs, cancellation and results
- telemetry ingestion and metrics
- releases, risk evaluation and risk history
- rollback policies, preview, execution and status
- incidents, audit history and AI explanations
- cleanup patch preview and GitHub PR creation

Use consistent response envelopes, validation errors, pagination, request IDs, rate limits and idempotency for mutating operations. Add authorization tests for every endpoint.

## 7. Frontend requirements

Create a polished, cohesive developer-tool interface. Use a premium dark theme with restrained accent colors, clear hierarchy, responsive layouts, accessible contrast and useful empty/loading/error states.

Main navigation:
1. Overview
2. Projects
3. Code Scanner
4. Dependency Map
5. Chaos Lab
6. Live Monitor
7. Release Guardian
8. Incidents
9. Cleanup Studio
10. Integrations
11. Policies
12. Settings

Dashboard should show actual backend data:
- connected Flagsmith status
- projects/environments
- latest scan and findings
- dependency graph summary
- simulation runs
- error/latency trends
- current incidents
- rollback actions and verification status

Do not use fake metrics in production screens. Seed demo data only through an explicit demo mode and visibly label it.

## 8. Deployment modes

### Self-hosted
Provide Docker Compose for:
- FlagForge web
- FastAPI API
- worker
- PostgreSQL
- Redis
- OpenTelemetry Collector
- optional Prometheus/Grafana
- optional Flagsmith services or documented external Flagsmith URL

Include `.env.example`, health checks, persistent volumes, migrations, backup/restore guidance, secure secret generation, reverse-proxy/TLS guidance and a one-command setup script. Do not bundle an insecure production default.

### Cloud
Provide containerized deployment guidance for:
- managed frontend hosting or container frontend
- API containers
- background workers
- managed PostgreSQL
- managed Redis
- managed secrets/KMS
- object storage if needed
- TLS, domain, backups, monitoring and scaling

Use the same codebase and schema in both modes. Configuration must determine deployment differences. Support either Flagsmith Cloud or a self-hosted Flagsmith instance.

## 9. Security and reliability

Implement:
- RBAC and organization isolation
- secure session/token handling
- encrypted credentials
- webhook signature validation and replay protection
- SSRF protection for user-supplied self-hosted URLs
- GitHub least-privilege permissions
- CSRF protection where applicable
- input validation and output encoding
- rate limiting
- secret redaction
- audit logging
- worker isolation and timeouts
- retries with backoff and dead-letter handling
- idempotent jobs and rollback actions
- database migrations and backup instructions

Never let an AI model or untrusted webhook directly execute privileged operations.

## 10. Development sequence

Build in milestones, keeping the repository runnable after each:

1. Monorepo, linting, Docker Compose, PostgreSQL, Redis, FastAPI health endpoint and Next.js shell.
2. Auth, organizations, projects, RBAC and migrations.
3. Real Flagsmith connection, test, sync, environment/flag display and webhook handling.
4. GitHub connection and safe static scanner for TypeScript/JavaScript and Python.
5. Dependency graph with evidence and confidence.
6. Demo app, OpenTelemetry telemetry and dashboard metrics.
7. Chaos Lab for isolated staging only, including snapshot and guaranteed restoration.
8. Deterministic risk engine and configurable policies.
9. Release Guardian with idempotency, locks, snapshots, verified rollback and audit.
10. AI explanations, Cleanup Studio, GitHub PR preview, cloud deployment, docs and end-to-end tests.

At each milestone:
- list files changed
- explain architecture choices
- provide exact run commands
- run tests and fix failures
- update README and `.env.example`
- avoid placeholders for claimed-complete features
- report honestly what is implemented versus deferred

## 11. Required deliverables

Produce:
- working monorepo
- Docker Compose self-hosted setup
- cloud deployment configuration/documentation
- database migrations
- OpenAPI API docs
- real Flagsmith adapter
- GitHub integration
- code scanner and dependency visualization
- demo app with feature-attributed telemetry
- isolated Chaos Lab
- deterministic risk engine
- policy-governed, verified rollback
- AI explanation adapter with no-AI fallback
- automated tests
- security documentation
- two detailed deployment READMEs:
  - `docs/SELF_HOSTED_QUICKSTART.md`
  - `docs/archive/FUTURE_CLOUD_DEPLOYMENT_DRAFT.md`
- root README with quick start and links

## 12. Acceptance criteria

The product is not complete until a clean environment can:
1. Start FlagForge and connect a real Flagsmith instance.
2. Display real projects, environments and flags.
3. Scan a supported repository and show source references.
4. Display a dependency graph with evidence labels.
5. Run a controlled staging simulation and restore its initial state.
6. Ingest demo application telemetry and show health metrics.
7. Calculate the same risk score for the same input.
8. Trigger a policy-eligible test rollback, update Flagsmith and verify the resulting state.
9. Refuse rollback when snapshot, telemetry, policy or concurrency checks fail.
10. Produce an incident explanation without giving AI control of actions.
11. Start through documented self-hosted steps and have a documented cloud deployment path.

Start by inspecting the existing repository and any parent-folder README/design documents before changing files. Preserve useful existing work. If no repository exists, scaffold it. First deliver the architecture decision record, repository skeleton, `.env.example`, Docker Compose development setup, and a working health-check path. Then proceed milestone by milestone. Ask only when a missing decision blocks safe implementation; otherwise choose sensible defaults and document them.
