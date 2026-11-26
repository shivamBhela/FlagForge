# Official Flagsmith local setup

## Upstream and deployment basis

This competition deployment uses the official [`Flagsmith/flagsmith`](https://github.com/Flagsmith/flagsmith) repository. Inspected release: `v2.295.2`, verified tag commit `5369ece3ff3aefbd021d2496f82a7ce0e9cd04d6`. Upstream's Docker configuration uses the combined dashboard/API image, PostgreSQL, a migration job and optional task processor. The root Compose configuration follows that topology, separates FlagForge and Flagsmith Postgres, and pins the official `2.295.2` multi-architecture image digest.

No upstream application source is copied or modified here; only Compose deployment definitions are adapted. The upstream README identifies the project as BSD 3-Clause licensed. References: [upstream README](https://github.com/Flagsmith/flagsmith/blob/v2.295.2/README.md), [upstream Compose](https://github.com/Flagsmith/flagsmith/blob/v2.295.2/docker-compose.yml), and [official Docker guide](https://docs.flagsmith.com/deployment-self-hosting/hosting-guides/docker).

## Initialize the local instance

Run `\.\setup.ps1` in PowerShell. Open [http://localhost:8081](http://localhost:8081); a fresh Flagsmith database shows initial administrator setup. Create the first admin and a dedicated demo organization/project. Create `Development`, `Staging`, and (for viewing only) `Production` environments. Use only a disposable competition organization.

Create flags such as `new_dashboard`, `beta_analytics`, `advanced_search`, `ai_recommendations`, `checkout_v2`, and `FLAGFORGE_LIVE_TEST`. Set the dedicated test flag ON in Development and Staging. Do not use production flags for Chaos Lab.

In Flagsmith Organization Settings, open **API Access** and create an Organization API key. Flagsmith's documented header is `Authorization: Api-Key <key>`; FlagForge sends it only from the backend. Do not log or publish the key.

## Connect FlagForge and synchronize

Create a FlagForge account/organization at [http://localhost:3000](http://localhost:3000), then open **Integrations**. Select **Flagsmith Local**. Use this internal URL:

```text
http://flagsmith:8000/api/v1
```

That Docker service name is intentional; `localhost:8081` is the host browser address, not the API container address. Paste the Organization API key into the password field, select **Test Connection**, then save and synchronize. Confirm the provider project, environments, feature definitions, and environment states appear in FlagForge.

Toggle only `FLAGFORGE_LIVE_TEST` OFF in the Flagsmith Development environment, sync again, and verify the new state in FlagForge. Sync once more and confirm there are no duplicate flags or states. Reload the FlagForge page and verify data persists.

## Optional demo app flag evaluation

The demo app is server-side. If a Flagsmith Development environment key is available, set `FLAGSMITH_ENVIRONMENT_KEY` in ignored local `.env`, restart/rebuild only the demo app, and test `/checkout`. This key is distinct from the Organization Management API key and must never be placed in `NEXT_PUBLIC_*` variables. With no key configured, the demo app must report evaluation unavailable and use only an explicitly labelled local fallback.

## Database and health

Flagsmith stores data in `flagsmith_postgres_data`; FlagForge uses `flagforge_postgres_data`. Flagsmith's official migration command runs in `flagsmith-migrate-db`; Alembic runs in `migrate`. Never point one application's database client at the other database.

Flagsmith liveness is `GET /health/liveness/`. The task processor uses the official `run-task-processor` command. A live process is not proof that an asynchronous business task succeeded; use its documented health/monitoring facilities when verifying processor work.

## Limitations

This is a local evaluation setup, not a hardened public deployment. Replace local secrets, restrict ports, configure TLS/backups and review current Flagsmith deployment documentation before non-local use. FlagForge worker queue, OTLP persistence, remote rollback, GitHub PR integration and native webhook compatibility are separate limits recorded in the final report.
