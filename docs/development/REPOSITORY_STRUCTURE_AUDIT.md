# Repository Structure Audit

Audit performed on `chore/repository-hygiene`, based on `origin/main` fetched 2026-11-28. Scope was limited to the requested development tooling and root documents. No application source, migrations, environment examples, deployment configuration, CI workflows, or Docker files were moved or removed.

## Item-by-item decisions

| Item | Purpose and usage | Reference/deletion risk | Decision |
| --- | --- | --- | --- |
| `.agent/` | Antigravity slash-command workflow definitions. These are consumed by the Antigravity development tool; they are not application runtime code. Workflows reference `.agents/` and `.gsd/`. | Removing or renaming breaks slash commands and the workflow paths. Install/update workflows also need to reflect the repository's current documentation layout. | **KEEP** at its convention-based path; update outdated guidance and copy paths. |
| `.agents/` | Agent definitions and reusable skills for planning, execution, verification, research and related development work. | `.agent/` workflow files refer to these paths, and the skill metadata uses the Agent Skills layout. Removing it breaks optional tool-assisted workflows. | **KEEP** at its convention-based path; correct default delegation and phase guidance. |
| `.gemini/` | Gemini-specific project instructions. `.gemini/GEMINI.md` links to canonical `PROJECT_RULES.md` and the moved Gemini adapter. | Gemini tooling discovers this convention-based file; its relative adapter link must remain valid. No application runtime imports it. | **KEEP** because Gemini remains a useful supported development tool. |
| `.gsd/` | Project specification, roadmap/state, historical phase plans and summaries, templates, examples and workflow artifacts. | GSD workflows and agents use these exact paths. Historical plans remain useful for traceability; stale references were repaired. | **KEEP** at its expected path; refresh only current-state claims and broken document links. |
| `adapters/` | Formerly held model-specific notes. Only Gemini had an active in-repository reference from `.gemini/GEMINI.md`; Claude and GPT OSS adapter files had no active consumers. | Removing the directory outright would remove Gemini-specific setup notes. Keeping unused adapters adds maintenance without an active tool link. | **MOVE** Gemini notes to `docs/development/ai-adapters/GEMINI.md`; **DELETE** unused `CLAUDE.md` and `GPT_OSS.md`. |
| `GSD-STYLE.md` | General development/workflow conventions consumed by several GSD workflows and `PROJECT_RULES.md`. | Removing without updating those references would break guidance links. Root duplication competed with the canonical project rules. | **MOVE** to `docs/development/AI_WORKFLOW_CONVENTIONS.md`; update active references. |
| `PROJECT_RULES.md` | Canonical repository-wide contributor and agent rules referenced by workflows, skills and Gemini instructions. | Renaming or overwriting it would break active references and discard project-specific direction. | **KEEP** at root as the canonical rules file. Install/update instructions now preserve it. |
| `PLAN.md` | Initial scaffold-era plan describing an obsolete Node.js monorepo direction. Not used by current application code or scripts. | No active executable consumer. Its historical context may explain early architecture decisions. | **ARCHIVE** as `docs/archive/LEGACY_INITIAL_PLAN.md`. |
| `FLAGFORGE_FULL_BUILD_PROMPT.md` | Original project-generation prompt; historical intent/spec context, not evidence that each requested feature was implemented. | The GSD requirements and first scaffold plan referenced the old root path; both now point to the archive path. | **ARCHIVE** as `docs/archive/ORIGINAL_BUILD_PROMPT.md`, explicitly labeled historical. |
| `README_CLOUD.md` | Aspirational cloud architecture/deployment draft; not the supported deployment guide and not evidence of a deployed public service. | No runtime/script dependency. Leaving it in the root could imply unsupported deployment instructions. | **ARCHIVE** as `docs/archive/FUTURE_CLOUD_DEPLOYMENT_DRAFT.md`, labeled unimplemented and historical. |
| `README_SELF_HOSTED.md` | Self-hosted Docker setup and local Flagsmith instructions. It duplicated parts of the main README and contained stale implementation claims. | Root README/setup instructions remain authoritative. No active runtime dependency on the filename. | **MOVE/UPDATE** as `docs/SELF_HOSTED_QUICKSTART.md`; retain the useful unique instructions and link from README. |

## Resulting root layout

The root remains focused on the services and essential project setup. Convention-based development tooling remains hidden at its required paths. Historical and development-only documentation now lives under `docs/`.

```text
FlagForge/
├── .agent/                 # Antigravity slash commands
├── .agents/                # Optional agent definitions and skills
├── .gemini/                # Gemini-specific instructions
├── .gsd/                   # Project state, plans, templates and history
├── backend/
├── demo-app/
├── docs/
│   ├── archive/            # Historical/unimplemented documents
│   ├── development/        # Workflow conventions and AI tooling notes
│   └── SELF_HOSTED_QUICKSTART.md
├── frontend/
├── scripts/
├── docker-compose.yml
├── .env.example
├── PROJECT_RULES.md
├── README.md
├── setup.ps1
├── setup.sh
└── essential project configuration
```

`origin/main` does not contain a root `cli/` or `.github/` directory. The CLI exists on the separate completion branch; this cleanup does not pull application code across branches. `adapters/` is removed after moving the sole referenced adapter. Docker, database, migrations, environment configuration, and application directories were retained.

## Evidence boundaries

The updated `.gsd/STATE.md`, `.gsd/ROADMAP.md`, and `.gsd/REQUIREMENTS.md` summarize the existing 2026-11-28 QA report as historical evidence from `completion/final-readiness`; they do not claim that those tests were rerun on this documentation branch. Fresh checks for this branch are recorded with the pull request and final response.
