# Security Review

**Date:** 2026-11-28
**Scope:** Static review of the local FlagForge repository and Docker Compose deployment, backend automated checks, and local QA behaviors. This is not a penetration test or independent security audit.

## Findings and changes

- **Ingress:** published Compose ports now bind to `127.0.0.1`, including FlagForge, Flagsmith, database, Redis, demo and OTel receiver ports. Docker-internal traffic continues to use the Compose network. This avoids accidental LAN exposure by default; it does not provide TLS or protect against other local processes/users.
- **Flagsmith webhook SSRF:** the pinned Flagsmith 2.295.2 validator honors the supported `SSRF_ALLOWED_HOSTS` exact-host setting. Compose trusts only the DNS alias `api.flagforge.local`, which is scoped to the Compose network. The live test verified a signed provider event and two Staging-only flag updates. All other outbound callback hosts remain subject to the provider's SSRF checks; do not broaden this allowlist.
- **GitHub credentials:** fine-grained tokens are encrypted at rest using FlagForge's existing secret encryption. App private key is server-side environment configuration. Credentials are never returned to browser responses. Recommended permissions are Metadata read, Contents read/write and Pull requests write, scoped to a single test repository. No credentials are present in this checkout.
- **API safety:** organization authorization is required for integration configuration and PR actions. Repository names are checked against the authenticated repository listing. Cleanup PR flow writes a single reviewed file to a non-default branch, rechecks base commit and file SHA, requires explicit approval, never merges, and records PR metadata. API mock/tenant tests pass; external GitHub behavior remains unverified.
- **Authentication and tenant boundaries:** test suite covers JWT, password authentication, role checks and tenant isolation. These are automated checks, not a security audit.
- **Login throttling:** `/auth/login` uses Redis atomic counters keyed by HMAC-hashed IP/account identifiers, with an eight-attempt account/IP window and a 100-attempt IP ceiling over 15 minutes. It returns 429 with `Retry-After` and fails closed with 503 if Redis is unavailable. Unit tests cover lockout, successful-login reset, and Redis outage. The rebuilt local API was also verified against real Compose Redis: eight invalid attempts returned 401 and the ninth returned 429 with `Retry-After`.
- **SSRF:** existing Flagsmith connection URL policy rejects loopback, link-local, reserved, metadata and unallowlisted private addresses. Automated SSRF matrix passed.
- **Webhook authenticity:** raw-body HMAC signature verification, replay protection and tenant-scoped processing are implemented and automated-tested. Signing secrets are encrypted at rest; migration 009 upgrades legacy values and receiver code accepts them during rollout. A provider-signed test callback and real Staging flag updates were processed and synchronized. The temporary signing secret was cleared and provider webhook removed.
- **Frontend dependencies:** Next.js 16.4.6 and PostCSS 8.5.33 overrides are pinned in the lockfile; `npm audit` and `npm audit --omit=dev` report zero known vulnerabilities as of the assessment date. Dependency audit does not replace a security review.
- **Data and logging:** local `.env` is gitignored; no credential values are included in this report. GitHub errors are sanitized. Review future logs and bug reports before sharing. The local Flagsmith service emits upstream Django Axes configuration warnings; address those settings as part of deployment review.

## Operational items before any shared or production deployment

1. Terminate TLS at a trusted ingress and restrict ingress to intended users/networks.
2. Store secrets in a managed secret store; rotate JWT/encryption keys and provider credentials with a tested overlap procedure.
3. Define token expiry and Flagsmith management-key rotation. Confirm a replacement works before revoking a key still used by the demo.
4. Back up both PostgreSQL databases and Redis persistence as required; perform a restore drill.
5. Configure production CORS, review rate-limit thresholds against deployment traffic, database roles, Redis authentication/network policy, monitoring and incident response.
6. Run an independent threat model and penetration test against the intended deployment.

The local stack remains a development/demo deployment and is not production-ready.
