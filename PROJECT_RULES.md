<!-- GSD Project Profile: WEB -->
# PROJECT_RULES.md — Canonical Development Rules

This file is the canonical, model-independent set of FlagForge development rules. Tool-specific workflows may add commands, but they must not contradict these rules.

## Working approach

1. Read the user's request and the relevant repository state.
2. Make one focused implementation plan per request when a plan is useful.
3. Do not turn ordinary tasks into phases, waves, roadmaps, ceremonies or separate plans.
4. Use a phased roadmap only when the user asks for it or the work is a genuinely large, multi-milestone effort with meaningful dependencies.
5. Implement, verify empirically, report limitations and commit safely when requested or appropriate.

A finalized specification is useful for a new project or a major milestone. It is not a gate for routine bug fixes, maintenance or focused changes.

## Preserve behavior and user work

- Inspect status and the relevant diff before editing.
- Preserve unrelated working-tree changes, local configuration and existing data.
- Never use destructive cleanup, reset, force-push or database/volume deletion unless explicitly authorized.
- Keep secrets out of source control, logs, screenshots and frontend bundles.
- Fix the smallest code path that addresses a verified defect.
- Do not claim tests, integrations or deployments passed without current evidence.

## Empirical verification

Choose checks that prove the requested change:

| Change | Evidence |
| --- | --- |
| API behavior | Automated test or actual HTTP request and response |
| UI behavior | Browser interaction and screenshot where useful |
| Build or types | Actual command output |
| Configuration | Parser, validator or runtime check |
| Integration | Real external round trip; label mocks and historical results |

Do not add or run unrelated tests just to inflate coverage. Report failures, skips and blocked checks accurately.

## Search-first reading

- Search for references before moving or removing a file.
- Read only relevant sections of large files until a full read is necessary.
- Check references, relative links, tooling conventions and runtime use before changing repository structure.

## Optional delegation

Subagents are optional helpers. Do not delegate by default, one per task or merely to create parallel activity. Work directly unless the user asks for delegation or the task has independent work that materially benefits from it and the available tools support it.

When delegation is used:

- Give the helper a clear bounded task and relevant constraints.
- Preserve workspace isolation for concurrent writers.
- Review its actual changes and verification before accepting them.
- Do not claim delegated work that did not happen.

The reusable delegation guidance is in .agents/skills/subagent-delegation/SKILL.md.

## Plans, phases and parallel work

A short plan may be useful for a multi-file change. Keep it focused on the requested outcome.

Phases, waves and roadmap artifacts are optional organizational tools for large milestones. For ordinary tasks, work through one plan directly. Within a large milestone, use dependency groups only when they clarify real ordering or safe parallel work; do not invent artificial groupings.

## State and notes

Update .gsd/STATE.md when a substantial project decision or verified project state changes. Do not require a state snapshot after every task, commit or internal grouping. Keep historical notes labeled as historical and date current verification.

## Model-independent guidance

Instructions describe capabilities and outcomes, not a required model, vendor or model tier. Optional tool-specific notes live in docs/development/ai-adapters/. They must not duplicate or override this file.

## Commits

Use descriptive Conventional Commit messages when committing, such as chore(repo): clarify development documentation.

- Inspect staged changes before committing.
- Stage only files related to the requested work.
- Never commit credentials, local databases, recordings, screenshots or generated test data unless explicitly requested.
- Verify the new commit and remote result when publishing.
- Do not force-push or merge unless explicitly authorized.

## Shell and platform support

Workflows should prefer portable commands or show correct PowerShell and POSIX examples. Run one shell command at a time where shell parsing or side effects could make chaining ambiguous. Inspect exit codes and output before treating a command as successful.

## Repository structure

- PROJECT_RULES.md: canonical development rules
- .agent/workflows/: Antigravity slash-command workflows
- .agents/agents/ and .agents/skills/: optional agents and reusable skills
- .gemini/: Gemini-specific guidance
- .gsd/: project state, requirements, roadmap and historical plans
- docs/development/: development conventions and AI tooling notes
- docs/archive/: clearly labeled historical material
- backend/, frontend/, demo-app/, scripts/: application and operational code
- docs/: setup, architecture, security and QA documentation

## Context management

Load context when it helps the task. Search first, summarize large findings when useful and continue in the current session unless a genuine need for a fresh session exists. Do not impose token-percentage gates, forced pauses or one-plan-per-session rules.

## Quick reference

- Ordinary request: one focused plan at most; no automatic phases or subagents.
- Large milestone: phase it only when requested or when real dependencies require it.
- Before changes: inspect status, references and relevant code.
- Before completion: run relevant verification and report actual limits.
- Before commit: inspect the staged diff and keep local secrets/artifacts out.
