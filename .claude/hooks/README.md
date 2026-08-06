# Hooks

Hooks are *registered* in `.claude/settings.json`, not by dropping files here.
This folder holds the scripts those registrations point at, so the config stays
one line per hook.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/check-claims.sh" }
        ]
      }
    ]
  }
}
```

The hook receives the event as JSON on stdin and signals through its exit code:
`0` proceeds, `2` blocks the action and feeds stderr back to Claude, anything
else is a non-blocking warning. Make scripts executable (`chmod +x`).

Events: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`,
`SubagentStop`, `SessionStart`, `SessionEnd`, `Notification`, `PreCompact`.

Hooks run shell commands automatically with your credentials — read a script
before registering it.

## Independent Codex review

`/review plan [focus]`, `/review refine [focus]`, and `/review test [focus]` use a
`UserPromptExpansion` hook, registered in `settings.json`. The hook receives the command name and
arguments, calls `codex-interview.sh`, and injects the report as context for Claude's expanded
command. It does **not** run for ordinary prompts or other slash commands.

`codex-interview.sh` accepts only those three modes and runs:

```bash
codex exec -s read-only --ephemeral -C <project-dir> <review-prompt>
```

That makes the reviewer an independent, non-persistent, read-only challenge pass. It may consume
Codex usage and can take several minutes; a failure is injected as unavailable review, not treated
as a pass. The script emits only hook JSON on stdout because Claude Code parses stdout as the hook
response.

Candidate for this repo: a `PostToolUse` check that flags an edit to
`FINDINGS.md` adding a claim with no VERIFIED / INFERRED / CANNOT VERIFY tag.
