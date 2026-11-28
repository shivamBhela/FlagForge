# AI Workflow Conventions

These notes complement the canonical [PROJECT_RULES.md](../../PROJECT_RULES.md). Keep the instructions model-independent.

## Plan at the scale of the request

- Start with one clear objective and one focused plan.
- Handle ordinary work directly; do not create phases or waves by default.
- Use a roadmap only for a requested or genuinely large milestone with multiple deliverables or dependencies.
- Treat 2–3 tasks per plan as a sizing hint, not a hard limit.
- Add dependency groups only when actual ordering or safe parallel work requires them.

## Use helpers deliberately

- Work directly for a contained change.
- Delegate only when requested or when separate workstreams materially benefit from parallel help.
- Do not create one helper per plan or force a fresh session for each task.
- Review helper output and rerun relevant verification yourself before accepting changes.

## Preserve evidence and safety

- Inspect repository status and search references before editing or moving files.
- Verify with the narrowest meaningful test first, then run related regression checks.
- Keep evidence concise and reproducible. Distinguish real integrations, mocks, synthetic data and historical checks.
- Keep credentials, local configuration and generated test artifacts out of Git.
- Commit only reviewed changes. Never force-push or delete user data to obtain a clean result.

## Tool compatibility

Antigravity slash commands remain in [.agent/workflows/](../../.agent/workflows/). Optional agent definitions and skills remain in [.agents/](../../.agents/). Project artifacts and phase history remain in [.gsd/](../../.gsd/).

Gemini-specific notes are kept in [ai-adapters/GEMINI.md](ai-adapters/GEMINI.md). Tool-specific guidance may describe a capability, but it must not require a particular model provider or override PROJECT_RULES.md.
