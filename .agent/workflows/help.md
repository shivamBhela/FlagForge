---
description: Show all available GSD commands
---

# /help Workflow

<objective>
Display all available GSD commands with descriptions and usage hints.
</objective>

<process>

**First, read and display the version:**

**PowerShell:**
```powershell
$version = Get-Content "VERSION" -ErrorAction SilentlyContinue
if (-not $version) { $version = "unknown" }
```

**Bash:**
```bash
version=$(cat VERSION 2>/dev/null || echo "unknown")
```

**Then display help with version in header:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► HELP (v{version})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORE WORKFLOW
─────────────
/map              Analyze codebase → ARCHITECTURE.md
/plan [N]         Make one focused plan; pass N for an explicit roadmap phase
/execute [N]      Execute an explicitly planned phase
/verify [N]       Must-haves validation with proof
/debug [desc]     Systematic debugging (3-strike rule)

PROJECT SETUP
─────────────
/new-project      Deep questioning → SPEC.md
/new-milestone    Create milestone with phases
/complete-milestone   Archive completed milestone
/audit-milestone  Review milestone quality

PHASE MANAGEMENT
────────────────
/add-phase        Add phase to end of roadmap
/insert-phase     Insert phase (renumbers subsequent)
/remove-phase     Remove phase (with safety checks)
/discuss-phase    Clarify scope before planning
/research-phase   Deep technical research
/list-phase-assumptions   Surface planning assumptions
/plan-milestone-gaps      Create gap closure plans

NAVIGATION & STATE
──────────────────
/progress         Show current position in roadmap
/pause            Save state for session handoff
/resume           Restore from last session
/add-todo         Quick capture idea
/check-todos      List pending items

UTILITIES
─────────
/help             Show this help

───────────────────────────────────────────────────────

QUICK START
───────────
1. /new-project      → Initialize project context
2. /plan             → Make one focused plan by default
3. Implement and verify the requested work
4. Use /plan N and /execute N only for a requested or genuinely large milestone
5. Repeat

───────────────────────────────────────────────────────

CORE RULES
──────────
🧭 Use phases only when requested or genuinely needed
💾 Update STATE.md when substantial project state changes
🤝 Subagents are optional helpers, never a default requirement
✅ Empirical Valid.  Proof required, no "it should work"

───────────────────────────────────────────────────────

📚 Docs: docs/development/AI_WORKFLOW_CONVENTIONS.md, .gsd/examples/

───────────────────────────────────────────────────────
```

</process>
