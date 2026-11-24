---
phase: 3
plan: 1
wave: 1
gap_closure: false
---

# Plan 3.1: Complete Flagsmith Integration & Synchronization Engine

## Objective
Implement the production-grade Flagsmith integration for FlagForge: secure connection management supporting Flagsmith Cloud and self-hosted instances with Fernet credential encryption at rest and SSRF prevention; asynchronous Flagsmith Management API adapter; robust synchronization engine for remote projects, environments, feature flags, and feature states with full idempotency; background sync job tracking and deduplication; secure HMAC-SHA256 webhook ingestion; and complete frontend UI for managing connections, inspecting synchronized flags, viewing sync history, and driving the Mission Control dashboard.

## Context
Load these files for context:
- .gsd/SPEC.md
- .gsd/ROADMAP.md
- .gsd/REQUIREMENTS.md
- .gsd/STATE.md
- backend/app/models/
- backend/app/core/config.py
- backend/app/core/security.py

## Tasks

<task type="auto">
  <name>Encryption Service & SSRF Protection</name>
  <files>
    backend/app/core/crypto.py
    backend/app/core/ssrf.py
    backend/tests/test_crypto_ssrf.py
  </files>
  <action>
    Implement symmetric Fernet credential encryption and decryption utility using app settings ENCRYPTION_KEY.
    Implement SSRF validation utility that parses URLs, resolves hosts, and strictly blocks:
    - Loopback addresses (127.0.0.0/8, ::1)
    - Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Link-local and cloud metadata addresses (169.254.0.0/16)
    - Non-HTTP(S) schemes
    Write automated unit tests to prove encryption roundtrip and SSRF blocking.
  </action>
  <verify>
    python -m pytest backend/tests/test_crypto_ssrf.py -v
  </verify>
  <done>
    Credentials encrypt/decrypt deterministically and SSRF protection rejects all internal/metadata addresses while allowing public hostnames.
  </done>
</task>

<task type="auto">
  <name>Flagsmith Models & Database Migrations</name>
  <files>
    backend/app/models/flagsmith.py
    backend/app/models/feature_flag.py
    backend/app/models/__init__.py
    backend/alembic/versions/002_flagsmith_schema.py
  </files>
  <action>
    Create domain models:
    - FlagsmithConnection (id, organization_id, name, api_url, encrypted_token, connection_type [CLOUD, SELF_HOSTED], status [CONNECTED, ERROR, DISCONNECTED], webhook_secret, last_synced_at, last_error)
    - FeatureFlag (id, project_id, flagsmith_feature_id, name, key, description, type, default_enabled, is_archived, created_at, updated_at)
    - FeatureFlagState (id, feature_flag_id, environment_id, enabled, value, flagsmith_feature_state_id, updated_at)
    - SyncHistory (id, organization_id, connection_id, status [PENDING, RUNNING, COMPLETED, FAILED], trigger [MANUAL, SCHEDULED, WEBHOOK], records_created, records_updated, records_unchanged, records_deleted, error_details, started_at, completed_at)
    - WebhookEvent (id, organization_id, connection_id, event_type, payload, status, created_at)
    Add foreign keys with cascade delete, indices on lookup keys, and unique constraints.
    Create Alembic migration 002_flagsmith_schema.py.
  </action>
  <verify>
    Verify model imports and Alembic migration definition.
  </verify>
  <done>
    Models instantiate properly with async SQLAlchemy 2.0 and migration 002 applies cleanly.
  </done>
</task>

<task type="auto">
  <name>Flagsmith API Client & Idempotent Sync Engine</name>
  <files>
    backend/app/services/flagsmith_client.py
    backend/app/services/flagsmith_sync.py
    backend/app/schemas/flagsmith.py
    backend/app/api/v1/endpoints/flagsmith.py
    backend/app/api/v1/endpoints/webhooks.py
    backend/app/api/v1/router.py
  </files>
  <action>
    Build FlagsmithClient with httpx.AsyncClient:
    - Test connection (/projects/)
    - Fetch remote projects, environments, features, and feature states
    - Timeout handling, retries, and error mapping
    Build FlagsmithSyncEngine:
    - Full & targeted sync
    - Idempotent upsert of projects, environments, flags, and states
    - Diff tracking (created, updated, unchanged, deleted)
    - SyncHistory logging and error capture
    Build Webhook service with HMAC-SHA256 signature verification and async reconciliation.
    Build REST endpoints under /api/v1/flagsmith and /api/v1/webhooks:
    - Connection CRUD and test endpoint
    - Sync trigger and status endpoints
    - Feature flags list and details endpoints
    - Sync history endpoint
    - Webhook receiver endpoint
  </action>
  <verify>
    python -m pytest backend/tests/test_flagsmith_integration.py -v
  </verify>
  <done>
    Complete integration test suite passes verifying connection testing, discovery, idempotent sync, webhook verification, and tenant isolation.
  </done>
</task>

<task type="auto">
  <name>Frontend Integrations, Flags & Sync Dashboard</name>
  <files>
    frontend/src/app/integrations/page.tsx
    frontend/src/app/flags/page.tsx
    frontend/src/components/Sidebar.tsx
    frontend/src/app/page.tsx
    frontend/src/lib/api.ts
  </files>
  <action>
    Build Frontend screens with dark theme and responsive layout:
    - Integrations Page (/integrations): Connection cards, Add Connection modal (Cloud/Self-Hosted, URL, Token, Webhook Secret), Test Connection button, Sync button, Disconnect.
    - Feature Flags Page (/flags): Live synchronized flags list across projects & environments, search, environment toggle state pills, targeting metadata, sync status.
    - Update Mission Control Overview (/) to reflect real connected Flagsmith instance, synced flags count, and sync timestamps.
    - Update Sidebar with Flags navigation link.
  </action>
  <verify>
    cd frontend && npx tsc --noEmit && npm run build
  </verify>
  <done>
    Frontend builds with zero TypeScript errors and all routes generate optimized static/dynamic pages.
  </done>
</task>

## Must-Haves
After all tasks complete, verify:
- [ ] Stored Flagsmith credentials are encrypted at rest with Fernet
- [ ] SSRF validator blocks private, loopback, and cloud metadata IP destinations
- [ ] Flagsmith Management API adapter tests and synchronizes remote resources
- [ ] Sync engine is strictly idempotent (no duplicate flags on repeated sync)
- [ ] Webhook receiver verifies HMAC signatures and ignores invalid payloads
- [ ] Frontend displays real connection status, synchronized flags, and history
- [ ] All automated tests pass with 100% pass rate
