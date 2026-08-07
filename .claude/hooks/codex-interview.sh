#!/bin/bash
# Independent, read-only challenge review. Two callers, two invocation shapes.
#
#   Hook mode — zero positional arguments, UserPromptExpansion JSON on stdin.
#     Serves the /review command. Accepts exactly the three modes documented in
#     .claude/commands/review.md: plan, refine, test. Returns the report as
#     hookSpecificOutput.additionalContext and always exits 0.
#
#   CLI mode — invoked directly with arguments. Two gates, one per half of the pipeline:
#     bash .claude/hooks/codex-interview.sh refine    <doc-path> [source-path] [focus]
#     bash .claude/hooks/codex-interview.sh implement <spec-path> [focus]
#
#     `refine` with a path is the DOCUMENT gate — it serves /spec (SPEC.md against its
#     BRIEF.md) and /plan-team (PLAN-TEAM.md against its SPEC.md), before anything is
#     built. It judges whether the document answers the source it was written against and
#     names the gaps, technical and in the reasoning. Ends `VERDICT: READY TO BUILD |
#     GAPS | NOT READY`.
#
#     `implement` is the BUILD gate — it serves /execute:implement §8 and /execute:team
#     §6, after the builders are finished, and validates the diff against the spec it
#     claims to satisfy. Ends `VERDICT: MATCHES SPEC | DEVIATES | CANNOT TELL`.
#
#     Both print a plain-text report (no JSON wrapper) and exit non-zero when Codex did
#     not run. Neither writes a file: the caller reads the report and acts on it.
#
# The discriminator is argument count, not `[ -t 0 ]` — stdin is not a terminal inside a
# Bash tool call either, so a TTY test would misroute and then block forever on `cat`.
#
# `implement` is deliberately CLI-only: /review documents three modes and must keep
# rejecting a fourth, so hook-mode validation is unchanged. `refine` is the same mode in
# both invocations — with no path it is /review's generic spec challenge, with a path it is
# the document gate. A fifth mode name for the same job would be the parallel vocabulary
# CLAUDE.md forbids.
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
doc=""
source_doc=""

# Positional parsing is deferred until after the mode is validated, because the shape
# differs per mode — `implement <spec> [focus]` versus `refine <doc> [source] [focus]` —
# and shifting here would swallow refine's source path into the focus string.
if [ "$#" -gt 0 ]; then
  invocation="cli"
  mode="${1:-}"
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

# Operator kill switch, one file for both callers. While `.claude/codex-review.disabled`
# exists Codex is never launched; delete that file to re-enable. It reports the reviewer as
# *unavailable*, never as a pass — the repo's rule is that an unavailable reviewer is
# unknown, so CLI mode still exits 3 and a build run under it cannot be called validated.
if [ -f "$repo/.claude/codex-review.disabled" ]; then
  disabled_msg="Codex review is DISABLED by the operator (.claude/codex-review.disabled exists). \
The reviewer did not run, so this is an UNAVAILABLE opinion, not a pass. Re-enable by deleting \
that file. Do not present anything as reviewed or as spec-validated on the strength of this."
  if [ "$invocation" = "hook" ]; then
    DISABLED_MSG="$disabled_msg" python3 -c '
import json
import os

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptExpansion",
        "additionalContext": os.environ["DISABLED_MSG"],
    }
}))
'
    exit 0
  fi
  printf '%s\n' "$disabled_msg" >&2
  exit 3
fi

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
    echo "Usage: codex-interview.sh refine <doc-path> [source-path] [focus]" >&2
    echo "       codex-interview.sh implement <spec-path> [focus]" >&2
    echo "       codex-interview.sh <plan|refine|test> [focus]" >&2
    exit 2
    ;;
esac

# A path relative to the repo root resolves against it; an absolute path is taken as given.
# Echoes the absolute path, or exits 2 naming the file that is not there — a gate that
# silently reviewed the wrong file would be worse than one that did not run.
resolve_path() {
  local given="$1" label="$2" abs="$1"
  case "$abs" in
    /*) ;;
    *) abs="${repo}/${given}" ;;
  esac
  if [ ! -f "$abs" ]; then
    echo "Codex review was not run: no ${label} at '${given}'." >&2
    exit 2
  fi
  printf '%s' "$abs"
}

if [ "$invocation" = "cli" ]; then
  case "$mode" in
    implement)
      spec="${2:-}"
      if [ "$#" -gt 2 ]; then shift 2; focus="$*"; fi
      ;;
    refine)
      doc="${2:-}"
      source_doc="${3:-}"
      if [ "$#" -gt 3 ]; then shift 3; focus="$*"; fi
      ;;
    *)
      if [ "$#" -gt 1 ]; then shift 1; focus="$*"; fi
      ;;
  esac
fi

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
    if [ -z "${doc:-}" ]; then
      # No path: /review's generic challenge, unchanged. This is the hook path.
      mode_prompt=$'Review the current specification or proposed refinement. Check for contradictions, untestable claims, scope creep, missing failure behaviour, unrecorded assumptions, and whether the change remains traceable to evidence and the case-study brief.'
    else
      # Both resolutions are fail-fast assertions, not values: Codex reads the files itself
      # from the paths in the prompt, so what matters here is that a wrong path stops the
      # gate rather than producing a confident review of a file that is not there.
      resolve_path "$doc" "document" >/dev/null || exit 2
      source_note=$'(none supplied — judge it against the case-study brief in docs/brief/ and against docs/analysis/FINDINGS.md, and say in your report that no source document was named)'
      if [ -n "${source_doc:-}" ]; then
        resolve_path "$source_doc" "source document" >/dev/null || exit 2
        source_note="$source_doc"
      fi

      mode_prompt=$'Validate a planning document against the source it was written from. Nothing has been built yet: this gate decides whether the document is fit to build from, and killing weak work here is cheaper than discovering it in the diff.\n'
      mode_prompt+=$'Read the document and its source in full before judging. Your first question is whether the document answers its source: every open question, option and decision the source left unresolved must be resolved here WITH A REASON. In this repository a document that leaves one open is not ready — a spec with an open decision is a brief.\n'
      mode_prompt+=$'Then judge it as the kind of document it is. A spec owes: a locked scope table whose CUT rows carry reasons; required behaviour traceable to a finding in docs/analysis/FINDINGS.md; an explicit section on what the product does when it has no good answer; acceptance criteria that are checkable statements rather than adjectives; an honesty register; a build order that puts whatever could invalidate the plan FIRST; and a decision log. A team plan owes: lanes that cannot collide on the same files; a dependency graph read out of the spec\'s own build order rather than invented; work the spec reserves for the owner assigned to nobody; and acceptance criteria lifted from the spec, not newly written.\n'
      mode_prompt+=$'Report gaps in two named groups. TECHNICAL: what could not be built from this as written — an undefined contract or data shape, a missing failure or empty path, an acceptance criterion nothing described here could demonstrate, an ordering that deadlocks, a step placed after the thing that would invalidate it. REASONING: an assumption stated as background and never tested, an alternative rejected without a reason or never considered, scope that reappeared after being cut, a conclusion the cited evidence does not support.\n'
      mode_prompt+=$'Flag as high severity any claim that would not survive checking: a figure no script in this repository produces; a retired figure; one end of a band quoted as a point (the `nowhere` share is [43.2%, 64.7%]); a single accuracy number where both error rates are owed; and any statement about WHICH deals a query returned — search_log.csv carries results_shown as a count, there is no query-to-deal mapping and no relevance score, so such a claim was invented.\n'
      mode_prompt+=$'Judge the document as written. Do not rewrite it, do not draft replacement sections, do not propose an alternative design, and do not implement anything.\n'
      mode_prompt+=$'End with a final line in exactly this form: VERDICT: READY TO BUILD | GAPS | NOT READY'

      mode_context=$'\n\nDocument under review: '"$doc"$'\nWritten against: '"$source_note"
    fi
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
