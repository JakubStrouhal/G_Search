#!/bin/bash
# Maintain the mechanical frontmatter keys on unit files under docs/analysis/.
#
# Convention — exactly three keys, in this order:
#
#   ---
#   created: YYYY-MM-DD
#   updated: YYYY-MM-DD
#   note: One sentence — what changed and why. Overwritten in place, never appended.
#   ---
#
# WHAT THIS HOOK CAN AND CANNOT DO. It maintains `created` and `updated`, which are
# mechanical: a date is a fact a shell script can read off the clock. It cannot author
# `note`, because `note` says *why* a file changed, and only whichever command or model
# made the edit knows that. So the split is deliberate, not an omission: the hook stamps
# the dates and inserts a placeholder `note` on first sight, and the model overwrites the
# placeholder. The hook never touches a `note` again after that — a `note` written by a
# model is the only part of the block with any information in it, and a script that
# clobbered it would make the block worthless. `/brief`, `/spec`, `/chore` and
# `/implement` emit the whole block themselves, which makes this hook a no-op on the
# files they create. That is the intended steady state.
#
# SECOND KNOWN LIMITATION. This runs as PostToolUse, so it rewrites the file *after* the
# Write/Edit that triggered it. Inserting a block shifts every line down by five, and the
# harness's cached view of the file is now stale — a follow-up Edit on the same file can
# fail to match until the file is read again. Insertion only happens once per file, so
# this bites the first edit of a file and never again, but it does bite.
#
# THIRD. "Has frontmatter" is decided by line 1 being exactly `---`, plus a `created:` or
# `updated:` key inside the block. A markdown file whose body opens with a horizontal rule
# is therefore ambiguous; the key test is what keeps it from being written into. A file
# that genuinely opens with `---` and has neither key is left alone rather than guessed at.
#
# Two callers: the PostToolUse hook (JSON on stdin, zero positional args), and a direct
# call with the path as $1 (used by the tests). Exits 0 on every path, including every
# error — a hook that fails loudly on every edit is worse than no hook at all.

set -u

# --- resolve the target path ------------------------------------------------------
if [ "$#" -gt 0 ]; then
  file="$1"
else
  file=$(python3 -c '
import json
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    print("")
else:
    if isinstance(payload, dict):
        target = payload.get("tool_input") or {}
        print(target.get("file_path", "") if isinstance(target, dict) else "")
    else:
        print("")
' 2>/dev/null) || exit 0
fi

[ -n "${file:-}" ] || exit 0

# --- only unit files under docs/analysis/ -----------------------------------------
case "$file" in
  *docs/analysis/*.md) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] && [ -w "$file" ] || exit 0

today=$(date +%F) || exit 0
[ -n "$today" ] || exit 0

placeholder='note: Frontmatter stamped mechanically — replace with one sentence on what changed and why.'

first_line=$(head -n 1 "$file" 2>/dev/null) || exit 0

tmp=$(mktemp "${TMPDIR:-/tmp}/unit-frontmatter.XXXXXX") || exit 0

if [ "$first_line" = "---" ]; then
  # Existing block: find the closing delimiter, then update `updated` only.
  # `fm_end`, not `close` — `close` is a built-in function name in BSD awk and is a
  # syntax error as a variable there.
  fm_end=$(awk 'NR>=2 && NR<=41 && $0=="---" {print NR; exit}' "$file" 2>/dev/null)
  if [ -z "${fm_end:-}" ]; then
    rm -f "$tmp"
    exit 0
  fi

  awk -v fm_end="$fm_end" -v today="$today" '
    { L[NR] = $0 }
    END {
      looks_like_frontmatter = 0
      seen = 0
      insert_after = 1
      for (i = 2; i < fm_end; i++) {
        if (L[i] ~ /^created:/) { looks_like_frontmatter = 1; insert_after = i }
        if (L[i] ~ /^updated:/) { looks_like_frontmatter = 1; seen = 1 }
      }
      if (!looks_like_frontmatter) { exit 3 }

      for (i = 1; i <= NR; i++) {
        if (i >= 2 && i < fm_end && L[i] ~ /^updated:/) {
          print "updated: " today
        } else {
          print L[i]
        }
        if (!seen && i == insert_after) { print "updated: " today }
      }
    }
  ' "$file" >"$tmp" 2>/dev/null
  status=$?
else
  # No block: insert one, dated today, with a placeholder note for the model to overwrite.
  {
    printf -- '---\n'
    printf 'created: %s\n' "$today"
    printf 'updated: %s\n' "$today"
    printf '%s\n' "$placeholder"
    printf -- '---\n'
    printf '\n'
    cat "$file"
  } >"$tmp" 2>/dev/null
  status=$?
fi

if [ "$status" -ne 0 ] || [ ! -s "$tmp" ]; then
  rm -f "$tmp"
  exit 0
fi

# Idempotent: identical content is not rewritten, so mtime stays put.
if cmp -s "$tmp" "$file"; then
  rm -f "$tmp"
  exit 0
fi

cat "$tmp" >"$file" 2>/dev/null
rm -f "$tmp"
exit 0
