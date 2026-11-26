# Security notes for the local demonstration

- `.env` is ignored by Git. `setup.ps1` generates unique local secrets and does not overwrite an existing file. Do not paste `.env` values into chat or commit them.
- Flagsmith Management API credentials are entered through FlagForge and encrypted by the backend. Responses expose only a `has_token` boolean; logs must not contain credentials.
- The optional Flagsmith Environment Key is server-side demo-app configuration in `.env`. Never put it in `NEXT_PUBLIC_*` values or browser bundles.
- SSRF validation blocks localhost, loopback, link-local, cloud metadata, multicast, reserved, and arbitrary private destinations. Only exact hosts in `FLAGSMITH_ALLOWED_HOSTS` may resolve to RFC1918 addresses. The local default is the fixed Docker service name `flagsmith`.
- The two applications use different Postgres instances and named volumes. Do not share database credentials or run one application's migrations against the other's database.
- The local stack is not hardened for public exposure. Do not port-forward it. For non-local use, configure TLS, restrict access, backups, secret rotation and a deployment-specific review.
- No production Flagsmith organization is part of the local stack. Do not run Chaos Lab against production.
- Start/stop scripts do not remove existing containers or volumes. Avoid `docker compose down --volumes`; back up before intentional database deletion.

## GitHub credentials and local callbacks

Fine-grained GitHub tokens are encrypted at rest; GitHub App private keys remain server-side. Use a single QA repository and minimum permissions (Metadata read, Contents read/write, Pull requests write). Cleanup Studio requires a reviewed real-file diff and explicit approval, writes one file on a separate branch and opens a PR without merging. No GitHub credentials are configured in this environment, so the flow is mock-tested only.

The Docker Compose default binds host ports to loopback. The local callback exception is the exact Flagsmith hostname `api.flagforge.local` in `SSRF_ALLOWED_HOSTS`; it resolves only on the Compose network and Flagsmith's SSRF guard remains enabled for every other host. A signed provider test callback and Staging-only flag updates were verified locally. Reverify in each deployment environment.
