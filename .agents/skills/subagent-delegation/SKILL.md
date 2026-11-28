---
name: subagent-delegation
description: Optional guidance for using Antigravity subagents when requested or materially useful
---

# Optional Subagent Guidance

Work directly by default. Do not force helper agents, one-helper-per-plan rules or parallel work.

Use an Antigravity subagent only when the user asks for it or when independent workstreams materially benefit from a separate context and the available tools support that use. A contained task usually stays with the primary implementer.

When delegating:

- Check that invoke_subagent is available before relying on it.
- Give a bounded task, relevant paths, constraints and a clear return format.
- Do not put secrets or unnecessary file contents into prompts.
- Use isolated workspaces for concurrent writers; keep shared work read-only.
- Review actual edits and verification before accepting the result.
- Never claim work was delegated if no helper ran.

If the helper tool is unavailable or a helper fails, continue directly when safe and feasible. Normal direct work is not degraded mode and needs no warning.

Antigravity slash-command workflows remain in .agent/workflows/. The agent and skill definitions remain in .agents/agents/ and .agents/skills/.
