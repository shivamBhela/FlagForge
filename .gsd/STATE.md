# FlagForge Project State

## Current Position

- **Branch:** `fix/flagforge-engineering-remediation` (branched from `completion/final-readiness`)
- **Status:** Comprehensive engineering remediation complete across code scanner, security vulnerabilities, dependency intelligence, and simulation services.
- **Assessment Date:** 2026-11-28.
- **Test Suite Status:**
  - Backend pytest suite: **65 passed** (100% pass rate).
  - CLI pytest suite: **12 passed** (100% pass rate).
  - Frontend production build (Next.js 16.4.6 Turbopack): **20/20 routes compiled successfully**, zero TypeScript or linting errors.

## Remediated Capabilities

### 1. Priority 0: Code Scanner & AST Remediation
- **Real Source Scanning:** Replaced fake hardcoded example snippets with live public and authorized private GitHub zipball extraction via GitHub API.
- **Archive Security Enforcement:**
  - Whitelisted safe redirect domains (`github.com`, `codeload.github.com`, `api.github.com`).
  - Strict HTTPS validation, prohibiting userinfo in URLs.
  - Archive download and expanded size capped at 50 MB.
  - Zip traversal (Zip Slip) attack protection strictly rejecting `..` and absolute paths.
  - Automatic filtering of symlinks, binaries, and non-source directories (`.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`).
- **Python AST Parser:** Native `ast.NodeVisitor` detecting function, async function, and class scopes. Eliminates regex fallback on `SyntaxError` (unparseable Python is logged and safely skipped).
- **TypeScript / JavaScript Parser:** Pre-processing comment stripper removes single-line (`//`) and multi-line (`/* */`) comments while preserving newline structure, eliminating false-positive flag references.
- **Frontend Scanner Workflow:** Removed automatic demo repository creation on scan click. Provided clean repository registration modal and selection dropdown.

### 2. Priority 1: Security Fixes
- **Flagsmith Test Endpoint Hardened:** `/api/v1/flagsmith/test` and `/api/v1/flagsmith/organizations/{org_id}/test` strictly require authenticated users with Org Admin privileges (`require_org_admin`) and tenant context. Preserves SSRF defense; never leaks tokens.
- **Tenant IDOR Protection:** Enforced tenant ownership verification across scanner repository endpoints (`trigger_scan`, `get_repository`, `delete_repository`) with HTTP 404 on cross-organization access attempts.
- **Numerical Validation & Defensive Arithmetic:**
  - `RolloutPolicy` validated with Pydantic: weights `[0, 1]`, weights sum to 1.0, error rate threshold `(0, 1]`, latency threshold `> 100ms`.
  - `DeterministicRiskEngine` defended against division by zero, `NaN`, and `Inf`, cleanly bounding scores to `[0.0, 100.0]`.

### 3. Priority 2: Dependency Intelligence
- Replaced simplistic `.py` vs web file extension heuristic with evidence-backed service inference based on directory structure (`services/`, `apps/`, `backend/`, `frontend/`, repository metadata) and `UNCLASSIFIED` fallback.
- Implemented idempotent graph rebuilds: removes obsolete `INFERRED` edges when references disappear while preserving manual `EXPLICIT` edges.

### 4. Priority 3: Honest Placeholders & Simulation Semantics
- **Chaos Lab:** Explicitly marked as `SYNTHETIC_SIMULATION` with clear execution logs stating no provider state or application traffic is mutated.
- **AI Explanation:** Structured response labeled `advisory_only: True` with deterministic fallback.
- **Cleanup Studio:** Draft preview clearly marked; requires real GitHub credentials for PR generation.
- **Release Guardian:** Rollback remains strictly guarded and advisory until live verified writes are confirmed.

### 5. Priority 4: Companion CLI
- Companion CLI `flagforge` verified with secure local scanning, safe zip extraction, and Flagsmith CLI compatibility.
