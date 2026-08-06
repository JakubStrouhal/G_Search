# Subagents

One Markdown file per agent; the filename is the agent type:
`.claude/agents/claim-checker.md` → `subagent_type: "claim-checker"`.

```markdown
---
name: claim-checker
description: When this agent should be used — Claude reads this to decide
  whether to delegate, so state the trigger, not just the capability.
tools: Read, Grep, Bash          # optional; omit to inherit all tools
model: sonnet                    # optional; omit to inherit the session model
---

The agent's system prompt. It starts with a fresh context window and returns
only its final report, so tell it exactly what to return.
```

Subagents are for work whose *conclusion* matters more than its intermediate
output — broad searches, independent verification passes, parallel fan-out.

Candidate for this repo: an agent that re-runs `validate.py` and checks every
number quoted in `FINDINGS.md` / Part C against the script's actual output,
given the known drift documented in `CLAUDE.md`.
