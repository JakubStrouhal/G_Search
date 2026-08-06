#!/bin/bash
# Independent, read-only challenge review for the /review Claude command.
#
# Claude Code supplies UserPromptExpansion JSON on stdin. This script accepts only
# the three review modes documented in .claude/commands/review.md, invokes Codex
# without persistent session state or write access, then returns its report as
# additionalContext for the command that Claude is about to receive.

set -u

hook_input=$(cat)
command_args=$(printf '%s' "$hook_input" | python3 -c '
import json
import sys

print(json.load(sys.stdin).get("command_args", ""))
')

read -r mode focus <<<"$command_args"
case "$mode" in
  plan|refine|test)
    ;;
  *)
    python3 -c '
import json

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptExpansion",
        "additionalContext": (
            "Codex review was not run. /review accepts exactly one mode: "
            "plan, refine, or test."
        ),
    }
}))
'
    exit 0
    ;;
esac

repo="${CLAUDE_PROJECT_DIR:-$(pwd)}"
focus_note=""
if [ -n "${focus:-}" ]; then
  focus_note=$'\nRequested focus: '"$focus"
fi

common_prompt=$'You are the independent interview reviewer for this repository.\n'
common_prompt+=$'Read the relevant repository state before judging. Treat CLAUDE.md and INDEX.md as operating context; preserve the VERIFIED / INFERRED / CANNOT VERIFY distinction.\n'
common_prompt+=$'Do not modify files, install dependencies, commit, or take external actions. Be adversarial but practical: identify only material gaps, cite exact files or sections, and distinguish verified facts from assumptions.\n'
common_prompt+=$'Return at most 700 words under: Verdict; What holds; Findings (severity, evidence, consequence); Questions or next checks.\n'

case "$mode" in
  plan)
    mode_prompt=$'Review the current proposed direction and its next planned action. Check whether the problem framing, evidence, scope, build order, acceptance criteria, and explicit cuts are sufficient to make a defensible decision before implementation. Prefer killing weak work early to polishing it.'
    ;;
  refine)
    mode_prompt=$'Review the current specification or proposed refinement. Check for contradictions, untestable claims, scope creep, missing failure behaviour, unrecorded assumptions, and whether the change remains traceable to evidence and the case-study brief.'
    ;;
  test)
    mode_prompt=$'Review the current implementation or test-ready change. Check whether the claimed behaviour can actually be demonstrated, whether the most consequential acceptance criteria have meaningful checks, and which unverified claims must not be presented as complete.'
    ;;
esac

review_prompt="$common_prompt"$'\nReview mode: '"$mode"$'\n'"$mode_prompt"$focus_note

set +e
review_output=$(codex exec -s read-only --ephemeral -C "$repo" "$review_prompt" 2>&1)
codex_status=$?
set -e

if [ "$codex_status" -ne 0 ]; then
  review_output="Codex reviewer did not complete (exit ${codex_status}). Claude should continue without treating this as review evidence. Diagnostic: ${review_output}"
fi

printf '%s' "$review_output" | python3 -c '
import json
import sys

report = sys.stdin.read().strip()
if len(report) > 9000:
    report = report[:9000] + "\n[Codex report truncated by hook]"

context = "Independent Codex review (mode: '"$mode"'):\n" + report
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptExpansion",
        "additionalContext": context,
    }
}))
'
