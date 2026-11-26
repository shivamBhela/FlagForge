# Current Verification and Follow-up

## Verified on 2026-11-26

- [x] Compose configuration and health check: 10 long-running services healthy; both migration jobs exit 0.
- [x] FlagForge migration head `009_encrypt_webhook_secrets`.
- [x] API-container backend suite: 35 passed, one upstream Starlette/httpx deprecation warning.
- [x] TypeScript check, Next.js 16 production build, and npm audit with zero vulnerabilities.
- [x] Headed Chromium workflow across all 18 routes; auth, persistence, org/project/environment, synthetic Chaos, filters, mobile viewport and error checks.
- [x] Local Flagsmith Staging signed webhook test and real flag-change/restore delivery; state read-back confirmed; temporary webhook and secret cleaned up.
- [x] GitHub PR workflow implementation and mocked API/tenant tests; live GitHub remains blocked by missing credentials.
- [x] Local Redis worker/restart recovery, Flagsmith sync, OTLP persistence, Monitor and Risk Engine evidence from prior QA runs.
- [x] Setup script checks `.env`-configured ports; Compose supports isolated project names and generated service names.

## Pending

- [x] Run documented setup in a clean isolated checkout with separate volumes; retain the existing default volumes.
- [x] Update reports with clean-checkout result. Commit the final evidence docs after restoring and verifying the default deployment.
- [ ] Reduce the 34 ESLint findings (15 state-in-effect, 14 dependency arrays, two internal navigation, two unescaped-text and one immutability). Do not weaken lint rules to clear the count.
- [ ] Verify GitHub integration against an explicitly authorized test repository when credentials are configured.
- [ ] Do not enable remote rollback until provider concurrency/conditional-write semantics, approval, audit and read-after-write can be safely guaranteed.
- [ ] Verify provider retry behavior, TLS/ingress, backup restoration and production deployment controls before any external exposure.
