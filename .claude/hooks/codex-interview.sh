#!/bin/bash
# Independent, read-only challenge review. Two callers, two invocation shapes.
#
#   Hook mode — zero positional arguments, UserPromptExpansion JSON on stdin.
#     Serves the /review command. Accepts exactly the three modes documented in
#     .claude/commands/review.md: plan, refine, test. Returns the report as
#     hookSpecificOutput.additionalContext and always exits 0.
#
#   CLI mode — invoked directly with arguments:
#     bash .claude/hooks/codex-interview.sh implement <spec-path> [focus]
#     Serves /implement's final step. Accepts the three review modes plus `implement`,
#     which validates a finished build against the spec it claims to satisfy. Prints a
#     plain-text report (no JSON wrapper) and exits non-zero when Codex did not run.
#
# The discriminator is argument count, not `[ -t 0 ]` — stdin is not a terminal inside a
# Bash tool call either, so a TTY test would misroute and then block forever on `cat`.
#
# `implement` is deliberately CLI-only: /review documents three modes and must keep
# rejecting a fourth, so hook-mode validation is unchanged.
#
# Codex runs read-only and ephemeral. It validates; it never implements. An unavailable
# reviewer is unknown, never a pass — in hook mode that is a diagnostic string in place of
# a report, and in CLI mode it is additionally a non-zero exit so the caller cannot
# mistake silence for approval.

set -u

repo="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)}"

mode=""
focus=""
spec=""

if [ "$#" -gt 0 ]; then
  invocation="cli"
  mode="${1:-}"
  spec="${2:-}"
  if [ "$#" -gt 2 ]; then
    shift 2
    focus="$*"
  fi
else
  invocation="hook"
  hook_input=$(cat)
  command_args=$(printf '%s' "$hook_input" | python3 -c '
import json
import sys

print(json.load(sys.stdin).get("command_args", ""))
')
  read -r mode focus <<<"$command_args"
fi

reject_hook() {
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
}

case "${invocation}:${mode}" in
  hook:plan|hook:refine|hook:test)
    ;;
  cli:plan|cli:refine|cli:test|cli:implement)
    ;;
  hook:*)
    reject_hook
    ;;
  *)
    echo "Codex review was not run: unknown mode '${mode}'." >&2
    echo "Usage: codex-interview.sh <plan|refine|test|implement> [spec-path] [focus]" >&2
    exit 2
    ;;
esac

focus_note=""
if [ -n "${focus:-}" ]; then
  focus_note=$'\nRequested focus: '"$focus"
fi

common_prompt=$'You are the independent interview reviewer for this repository.\n'
common_prompt+=$'Read the relevant repository state before judging. Treat CLAUDE.md and INDEX.md as operating context; preserve the VERIFIED / INFERRED / CANNOT VERIFY distinction.\n'
common_prompt+=$'Do not modify files, install dependencies, commit, or take external actions. Be adversarial but practical: identify only material gaps, cite exact files or sections, and distinguish verified facts from assumptions.\n'
common_prompt+=$'Return at most 700 words under: Verdict; What holds; Findings (severity, evidence, consequence); Questions or next checks.\n'

mode_context=""

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
  implement)
    if [ -z "${spec:-}" ]; then
      echo "Codex validation was not run: mode 'implement' requires a spec path." >&2
      echo "Usage: codex-interview.sh implement <spec-path> [focus]" >&2
      exit 2
    fi
    spec_abs="$spec"
    case "$spec_abs" in
      /*) ;;
      *) spec_abs="${repo}/${spec}" ;;
    esac
    if [ ! -f "$spec_abs" ]; then
      echo "Codex validation was not run: no spec file at '${spec}'." >&2
      exit 2
    fi

    mode_prompt=$'Validate a finished implementation against the specification it claims to satisfy. You are given the spec path and the diff of what was implemented. Read the spec in full, then read the changed files as they now stand in the repository.\n'
    mode_prompt+=$'For every MUST and HIGH row in the spec\'s scope table, judge implemented / partial / absent and cite the file and the evidence. Then check three things specifically: anything on the spec\'s CUT list that was built anyway; any acceptance criterion that what is here cannot demonstrate; and any number, mapping, category or description in the diff that is not traceable to the supplied data or to the spec.\n'
    mode_prompt+=$'Judge only what the diff and the repository show. Do not implement, patch, or write code, and do not propose an alternative design. If the diff is empty or does not correspond to the spec, say so rather than inferring what was probably built.\n'
    mode_prompt+=$'End with a final line in exactly this form: VERDICT: MATCHES SPEC | DEVIATES | CANNOT TELL'

    # `git diff` alone hides a build made of new files — most units here are still
    # untracked — so the status listing goes in beside it, and both are truncated
    # because the whole prompt is passed to codex as a single argv string.
    changes=$(
      {
        cd "$repo" 2>/dev/null || exit 0
        if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
          echo "(no git work tree at ${repo} — no diff available)"
          exit 0
        fi
        echo "--- git diff HEAD ---"
        git diff HEAD 2>/dev/null || echo "(git diff HEAD produced no usable output)"
        echo
        echo "--- git status --short (untracked and unstaged paths) ---"
        git status --short 2>/dev/null
      }
    )
    if [ "${#changes}" -gt 12000 ]; then
      changes="${changes:0:12000}
[diff truncated at 12000 characters — read the files in the repository for the rest]"
    fi
    if [ -z "${changes//[[:space:]]/}" ]; then
      changes="(no diff and no status output — the working tree reports no changes)"
    fi

    mode_context=$'\n\nSpec under validation: '"$spec"$'\n\nWhat was implemented:\n'"$changes"
    ;;
esac

review_prompt="$common_prompt"$'\nReview mode: '"$mode"$'\n'"$mode_prompt$focus_note$mode_context"

set +e
review_output=$(codex exec -s read-only --ephemeral -C "$repo" "$review_prompt" 2>&1)
codex_status=$?
set -e

if [ "$codex_status" -ne 0 ]; then
  review_output="Codex reviewer did not complete (exit ${codex_status}). Claude should continue without treating this as review evidence. Diagnostic: ${review_output}"
fi

if [ "$invocation" = "cli" ]; then
  printf '%s' "$review_output" | python3 -c '
import sys

report = sys.stdin.read().strip()
if len(report) > 9000:
    report = report[:9000] + "\n[Codex report truncated by hook]"

print("Independent Codex review (mode: '"$mode"'):")
print(report)
'
  # Unavailable is unknown, never a pass — the caller sees it in the exit status too.
  # Written as an `if`, not `[ … ] && exit 3`: under `set -e` a false AND-list is itself
  # a failing command, so the `&&` form would exit 1 on the success path.
  if [ "$codex_status" -ne 0 ]; then
    exit 3
  fi
  exit 0
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
