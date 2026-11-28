# Current Verification and Follow-up

## Verified on 2026-11-28

- [x] Compose configuration and health check: 10 long-running services healthy; both migration jobs exit 0.
- [x] FlagForge migration head `009_encrypt_webhook_secrets`.
- [x] API-container backend suite: 35 passed, one upstream Starlette/httpx deprecation warning.
- [x] Full frontend ESLint: all previously recorded 34 project findings fixed; zero findings.
- [x] TypeScript check, Next.js 16 production build, and npm audit with zero vulnerabilities.
- [x] Headed Chromium workflow across all 18 routes; auth, persistence, org/project/environment, synthetic Chaos, filters, mobile viewport and error checks.
- [x] Local Flagsmith Staging signed webhook test and real flag-change/restore delivery; state read-back confirmed; temporary webhook and secret cleaned up.
- [x] GitHub PR workflow implementation and mocked API/tenant tests; live GitHub remains blocked by missing credentials.
- [x] Local Redis worker/restart recovery, Flagsmith sync, OTLP persistence, Monitor and Risk Engine evidence from prior QA runs.
- [x] New worker stop/restart test: queued job completed, graceful SIGTERM verified, heartbeat removed, worker healthy after restart.
- [x] Critical-risk rollback recommendation test passed: rollback explicitly unavailable, manual approval required.
- [x] Setup script checks `.env`-configured ports; Compose supports isolated project names and generated service names.
- [x] Companion CLI scanner tests (5), CLI help, frontend lint, TypeScript, production build (20 routes), and production npm audit (0 vulnerabilities).

## Pending

- [x] Run documented setup in a clean isolated checkout with separate volumes; retain the existing default volumes.
- [x] Update reports with clean-checkout result. Commit the final evidence docs after restoring and verifying the default deployment.
- [x] Reduce the 34 ESLint findings without weakening lint rules.
- [ ] Complete Git Credential Manager browser sign-in, push `completion/final-readiness`, and verify the remote commit. The public remote is empty; `origin` is configured, but a noninteractive push check lacked credentials. No force-push or PR/merge has occurred.
- [ ] Recover Docker Desktop without removing volumes. Current Flagsmith restart is stuck at 0%, VM memory is 3.50/3.58 GB, and Docker CLI status calls time out.
- [ ] Fix the latest browser registration POST hang and rerun headed Playwright. Earlier E2E PASS does not replace the latest failure.
- [ ] Rerun API-container pytest after Docker recovers; host-only pytest is blocked because this host Python environment lacks `redis`.
- [ ] Do not enable remote rollback until provider concurrency/conditional-write semantics, approval, audit and read-after-write can be safely guaranteed.
- [ ] Verify provider retry behavior, TLS/ingress, backup restoration and production deployment controls before any external exposure.
