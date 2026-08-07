#!/bin/bash
# Orientation block: the INDEX.md "Now / Next" state plus what git knows.
#
# Two callers, one output:
#   - the SessionStart hook, whose stdout is injected into the new session's context
#     (this is what removes the need for a priming command);
#   - /wrap, which reads the same block before rewriting it.
#
# Read-only. Always exits 0 — it must never be able to fail a session start.

set -u
repo="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$repo" 2>/dev/null || exit 0

echo "# Repo state (auto-injected — .claude/hooks/session-state.sh)"
echo
echo "Authoritative status lives in INDEX.md. History lives in git, not in a hand-written log."
echo

if [ -f INDEX.md ]; then
  echo "## Now / Next (from INDEX.md)"
  echo
  awk '/<!-- state:start -->/{f=1;next} /<!-- state:end -->/{f=0} f' INDEX.md
  echo
  # Newest-first table: header, separator, then rows. Print the 3 most recent;
  # INDEX.md keeps 6. Bounds what every session pays for without shrinking the record.
  echo "## Recent decisions (3 most recent of 6 in INDEX.md — what was chosen and why)"
  echo
  awk '/<!-- decisions:start -->/{f=1;next} /<!-- decisions:end -->/{f=0} f' INDEX.md \
    | grep '^|' | head -5
  echo
  open=$(grep -c '| ⬜ |' INDEX.md 2>/dev/null || echo 0)
  echo "Open items in the INDEX.md pending queue: ${open}"
  echo
fi

echo "## Last commits"
git log --oneline -5 2>/dev/null || echo "(no git history)"
echo
echo "## Uncommitted"
git status --short 2>/dev/null | head -25
echo
echo "## Diff since HEAD"
git diff --stat HEAD 2>/dev/null | tail -12

exit 0
