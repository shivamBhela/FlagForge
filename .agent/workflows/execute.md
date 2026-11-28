---
description: The Engineer — Execute a specific phase with focused context
argument-hint: "<phase-number> [--gaps-only]"
---

# /execute Workflow

<role>
Execute the explicitly requested phase plan. Work directly by default; a gsd-executor helper is optional when requested or materially useful.
</role>

<objective>
Execute the requested phase plans in dependency order. Group work only when real dependencies require it. Direct execution is the default; helper delegation is optional.
</objective>

<context>
**Phase:** $ARGUMENTS (required - phase number to execute)

**Flags:**
- `--gaps-only` — Execute only gap closure plans (created by `/verify` when issues found)
- --delegate — Use an optional helper when delegation is requested or materially useful

**Required files:**
- `.gsd/ROADMAP.md` — Phase definitions
- `.gsd/STATE.md` — Current position
- `.gsd/phases/{phase}/` — Phase directory with PLAN.md files

**Delegation protocol:** `.agents/skills/subagent-delegation/SKILL.md`
**Subagent:** `.agents/agents/gsd-executor.md`
</context>

<process>

## 1. Validate Environment

**PowerShell:**
```powershell
Test-Path ".gsd/ROADMAP.md"
Test-Path ".gsd/STATE.md"
```

**Bash:**
```bash
test -f ".gsd/ROADMAP.md"
test -f ".gsd/STATE.md"
```

**If not found:** Error — user should run `/plan` first.

---

## 2. Validate Phase Exists

**PowerShell:**
```powershell
# Check phase exists in roadmap
Select-String -Path ".gsd/ROADMAP.md" -Pattern "Phase $PHASE:"
```

**Bash:**
```bash
# Check phase exists in roadmap
grep "Phase $PHASE:" ".gsd/ROADMAP.md"
```

**If not found:** Error with available phases from ROADMAP.md.

---

## 3. Ensure Phase Directory Exists

**PowerShell:**
```powershell
$PHASE_DIR = ".gsd/phases/$PHASE"
if (-not (Test-Path $PHASE_DIR)) {
    New-Item -ItemType Directory -Path $PHASE_DIR
}
```

**Bash:**
```bash
PHASE_DIR=".gsd/phases/$PHASE"
mkdir -p "$PHASE_DIR"
```

---

## 4. Discover Plans

**PowerShell:**
```powershell
Get-ChildItem "$PHASE_DIR/*-PLAN.md"
```

**Bash:**
```bash
ls "$PHASE_DIR"/*-PLAN.md 2>/dev/null
```

**Check for existing summaries** (completed plans):

**PowerShell:**
```powershell
Get-ChildItem "$PHASE_DIR/*-SUMMARY.md"
```

**Bash:**
```bash
ls "$PHASE_DIR"/*-SUMMARY.md 2>/dev/null
```

**Build list of incomplete plans** (PLAN without matching SUMMARY).

**If `--gaps-only`:** Filter to only plans with `gap_closure: true` in frontmatter.

**If no incomplete plans found:** Phase already complete, skip to step 8.

---

## 5. Review Plan Dependencies

Read `wave` field from each plan's frontmatter:

```yaml
---
phase: 1
plan: 2
wave: 1
---
```

Use explicit dependency fields to order work safely. If there are no meaningful dependencies,
execute plans directly without inventing wave groupings. Existing wave fields are historical
metadata unless they represent a real dependency.

Display execution order only when useful:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► EXECUTING PHASE {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Wave 1: {plan-1}, {plan-2}
Wave 2: {plan-3}

{X} plans in dependency order
```

---

## 6. Execute Plans

1. Execute the requested plans directly in dependency order.
2. Use a wave grouping only when it makes genuine dependencies or independent work clearer.
3. Use a subagent only when requested or when separate work materially benefits from one; Antigravity support is optional.
4. Run the verification for each task and preserve safe commit boundaries.
5. Write summaries only where the plan or project record requires them.

---

## 7. Verify Phase Goal

Check each phase must-have against the actual code and run its relevant verification. Direct verification is the default. An independent verifier helper may be used when requested or when a separate context materially increases confidence; label the evidence accordingly.

Record failed or blocked requirements without softening the result.

---

## 8. Update Roadmap and State

**Update ROADMAP.md:**
```markdown
### Phase {N}: {Name}
**Status**: ✅ Complete
```

**Update STATE.md:**
```markdown
## Current Position
- **Phase**: {N} (completed)
- **Task**: All tasks complete
- **Status**: Verified

## Last Session Summary
Phase {N} executed successfully. {X} plans, {Y} tasks completed.

## Next Steps
1. Offer the next phase only as an optional continuation; do not create or start it automatically.
```

**Update REQUIREMENTS.md** (if exists):
- Cross-reference completed tasks with requirement IDs
- Mark requirements satisfied by this phase as `In Progress` or `Complete`
- Update the traceability matrix with plan references

---

## 9. Commit Phase Completion

```bash
git add .gsd/ROADMAP.md .gsd/STATE.md .gsd/REQUIREMENTS.md
git commit -m "docs(phase-{N}): complete {phase-name}"
```

---

## 10. Offer Next Steps

</process>

<offer_next>
Output based on status:

**Route A: Phase complete, more phases remain**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► PHASE {N} COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{X} plans executed
Goal verified ✓

───────────────────────────────────────────────────────

▶ Optional continuation
The user may request planning or execution for another phase.

───────────────────────────────────────────────────────
```

**Route B: All phases complete**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► MILESTONE COMPLETE 🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All phases completed and verified.

───────────────────────────────────────────────────────
```

**Route C: Gaps found**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► PHASE {N} GAPS FOUND ⚠
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{X}/{Y} must-haves verified
Gap closure plans created.

/execute {N} --gaps-only — execute fix plans

───────────────────────────────────────────────────────
```
</offer_next>

<context_hygiene>
**After 3 failed debugging attempts:**
1. Stop current approach
2. Document to `.gsd/STATE.md` what was tried
3. Recommend `/pause` for fresh session
</context_hygiene>

<related>
## Related

### Workflows
| Command | Relationship |
|---------|--------------|
| `/plan` | Creates PLAN.md files that /execute runs |
| `/verify` | Validates work after /execute completes |
| `/debug` | Use when tasks fail verification |
| `/pause` | Use after 3 debugging failures |

### Skills
| Skill | Purpose |
|-------|---------|
| `executor` | Detailed execution protocol |
| `context-health-monitor` | 3-strike rule enforcement |
| `empirical-validation` | Verification requirements |
</related>
