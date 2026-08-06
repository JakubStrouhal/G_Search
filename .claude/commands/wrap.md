---
description: End-of-session close-out — reconcile INDEX.md with what this session actually did, then commit. Writes state, never a log.
argument-hint: ["one-line focus of the session"]  (optional — inferred from the conversation if absent)
allowed-tools: Bash(bash .claude/hooks/session-state.sh), Bash(git:*), Read, Edit
disable-model-invocation: true
---

Close out this session: $ARGUMENTS

## 1. Get the facts before writing anything

Run `bash .claude/hooks/session-state.sh`. That is exactly what the **next** session will be
handed on startup — you are editing what your successor reads, so judge every change by whether
it would orient someone who was not here.

Then read `INDEX.md` in full.

## 2. Separate what this session did from what is merely dirty

Cross-check the git output against this conversation. Other sessions leave dirty files; they are
not yours to claim. Work with no file edits still counts — a hypothesis killed, a direction
chosen, a number that turned out wrong — but it counts as a *decision*, not as a change.

## 3. Update `INDEX.md` — state only, in place

Exactly five kinds of edit are allowed. **Do not append a work-log entry; git owns history.**

- **Statuses in the Pending tables** — ⬜ → 🟡 → ✅. When flipping to ✅, replace the *Note* with
  what was actually established (a number, a file, a verdict), not "done".
- **Known issues** — add what this session broke or discovered; strike through and mark
  `**FIXED <date>**` what it fixed. Prune anything no longer true.
- **The `<!-- state:start -->` … `<!-- state:end -->` block** — rewrite it, don't extend it. Phase
  in one sentence, the top three ranked next actions, and what is deliberately *not* being done.
  Keep it under ~15 lines: it is injected into every future session, and a block nobody reads is
  worse than no block.
- **Board rows**, if a deliverable moved.
- **The `<!-- decisions:start -->` … `<!-- decisions:end -->` ring buffer** — one row, per
  `.claude/decision-row.md`, **only if this session decided something** a pipeline command did not
  already record. Adding a row deletes the oldest; the table stays at six. A session that executed
  an existing plan gets no row.

There is no frontmatter and no changelog — the file carries neither by design. A line about what
this session *did* belongs in the commit message; a line about what it *decided* belongs in the
ring buffer.

## 4. Findings are not status

If this session produced something a reader of the deliverable would need — a number, a corrected
claim, a killed hypothesis — it goes in `docs/analysis/FINDINGS.md` under its VERIFIED / INFERRED /
CANNOT VERIFY tag. `INDEX.md` records only *that* it happened. A finding that lives only in the
index is a finding Part C will not find.

## 5. Commit

One commit. Subject names the phase item it moved (`Phase 1.3: language test — 42.3pp gap`), body
lists what changed and what was left half-done. If the session genuinely moved nothing, say so and
commit nothing — an unchanged `INDEX.md` is a valid outcome and a fabricated update is worse than
none.

## 6. Report, ≤6 lines

Statuses flipped · known issues added or cleared · the one line you put in *Now / Next* · anything
dirty that was **not** yours · the single most important next action for whoever opens this repo
tomorrow.

> Honesty rule: half-done is recorded as half-done, and unverified is recorded as unverified. This
> file is only worth reading while it tells the truth — and this repo is a case study graded on
> whether claims survive checking, so the habit is the deliverable too.
