# Keeping track of the repo without re-priming every session

Decided 2026-08-05. Supersedes the ledger design that was originally written here (kept at the
bottom as *the version not built*).

---

## The shape

**Two moving parts, one file, no per-edit machinery.**

| | What | When |
|---|---|---|
| **Write** | `/wrap` → `.claude/commands/wrap.md` | You run it at the end of a session |
| **Read** | `SessionStart` hook → `.claude/hooks/session-state.sh` | Automatic, every new session |
| **The file** | `INDEX.md` — state only | — |
| **History** | `git log` | — |

The read side is what removes the priming step. `SessionStart` stdout is injected into the new
session's context, so the agent opens already knowing the phase, the ranked next actions, the last
five commits and what is dirty. Nothing has to be remembered and nothing is lost by forgetting.

**`/prime` (added 2026-08-05) does not undo that.** The hook prints the *Now / Next* block;
`/prime` reads the critical files behind it — `INDEX.md` in full, `FINDINGS.md`, and the current
`SPEC.md` — when a session is about to do real work. Opt-in and read-only; a
session that never types it is still correctly oriented.

## The three rules that keep it from rotting

**1. The index holds state, not history.** Everything in `INDEX.md` is overwritten in place and
pruned when resolved. Nothing is append-only. This is the change from the earlier design, and it
came from evidence: within one day, two sessions had both logged the same restructure and both
logged adding the same `README.md`. A hand-maintained work log duplicates itself the moment two
sessions run in parallel, and `git log` never does.

> **Amendment, 2026-08-06 — the Decisions ring buffer.** Rule 2 gives *what* to git, but git does
> not carry *why*: the SessionStart hook prints commit subjects, and a subject cannot hold the
> alternative that was rejected. So `INDEX.md` now carries six rows of `date · decision · why`
> between `<!-- decisions:start -->` / `<!-- decisions:end -->`, injected alongside *Now / Next*.
>
> **This is bounded state, not a log, and the distinction is the whole point.** Adding a row
> deletes the oldest, so the section has a fixed size and cannot accumulate — which is what rule 1
> actually requires. The thing that rotted before was unbounded growth, not the recording of
> decisions. Written by `/brief`, `/spec`, `/implement` and `/wrap`, each at most one row, and only
> when something was genuinely decided; see `.claude/decision-row.md`. Spreading the write across
> every pipeline command is deliberate — if only `/wrap` wrote it, a skipped `/wrap` would lose the
> decision, which is the exact staleness mode this system was built against.

**2. History is git.** `git log --oneline --stat` is an append-only, timestamped work log with the
diffs attached, written by a process that cannot forget. Anything you would have written in a log
entry belongs in the commit message. `/wrap` therefore ends in a commit — that *is* the log write.

**3. Findings are not status.** A number, a corrected claim, a killed hypothesis goes in
`FINDINGS.md`. The index records only that it happened. Otherwise the index slowly becomes the
document, and the actual deliverable goes stale beside it.

## Why not the hook-per-edit ledger

The original design attributed every `Write`/`Edit` to the slash command that caused it, via a
`UserPromptSubmit` → state-file → `PostToolUse` bridge, and rendered `INDEX.md` from the resulting
`ledger.jsonl`.

It is buildable and it has one real advantage — it cannot be forgotten. But:

- It needed an unverified assumption (that `UserPromptSubmit` sees `<command-name>` and
  `PostToolUse` does not) before anything could be built on it.
- It produces *facts* — "`/spec` touched 3 files at 14:02" — which is not what you need at
  session start. What you need is "the FINDINGS reconciliation is the next thing and here is why",
  and only the model can write that.
- Its output has to be summarised by something before it is readable, and the only good summariser
  is the model, which puts you back at `/wrap`.

**When to revisit it:** if you find you are skipping `/wrap` often enough that the index goes
stale, the ledger is the fix — it is the version that survives you forgetting. Build it then, with
the evidence of your own miss rate, not before. Design notes below.

<details>
<summary>The version not built — ledger design, kept for reference</summary>

Three hooks, one script, no model calls inside any of them.

1. **`UserPromptSubmit`** — parse `<command-name>/x</command-name>` out of `prompt`, write
   `{command, args, started_at}` to `.claude/state/<session_id>.cmd`. A non-command prompt clears
   it, so ordinary chat edits log as `command: null` instead of being misattributed.
2. **`PostToolUse`**, matcher `Write|Edit|MultiEdit|NotebookEdit` — read that file, append one JSON
   line to `.claude/state/ledger.jsonl` with ts / session / command / tool / path and ±lines from
   `git diff --numstat`. Never blocks; always exit 0.
3. **`Stop`** — run a renderer that rewrites only the machine-owned block of `INDEX.md`, delimited
   by markers. Exit 0, no nagging.

The principle it encodes, which is still the right one and is what `/wrap` implements manually:
**hooks record the fact, the model records the meaning.**

Two things that were going to be true either way:

- **Don't call `claude -p` from a hook** to generate summaries — slow, blocks the turn, and it
  commits text you never read. The `Stop` payload has `transcript_path`; the last assistant message
  is already a free summary if you want one.
- **Don't port an exit-2 nag that fires on "any dirty `.md`"** (the `wrap-up-reminder.sh` pattern
  in `~/Documents/NaParcele`). On an analysis repo it fires constantly and gets disabled within a
  day. If you want enforcement, make it narrow: fire only when a doc was created with no index row.

Command frontmatter that would make the board derivable rather than maintained — `id: SPEC-004`,
`status: draft|approved|in-progress|done|superseded`, `implements: SPEC-004` — is worth doing
independently of the ledger, once there are enough documents for a board to be the honest view.

</details>

## Portability

The two files here are generic: `session-state.sh` only assumes `INDEX.md` with `state:` markers,
and `wrap.md` only assumes the section names. Move both to `~/.claude/` and every repo gets the
same loop; the `INDEX.md` schema stays per-repo, because what "pending" means differs.

The existing `~/Documents/NaParcele` system is the same loop with more surface: `/context:wrap-up`
is `/wrap`, `PROGRESS.md` is `INDEX.md`. The two changes worth backporting are dropping the
append-only work log in favour of git, and replacing the `Stop`-hook nag with a `SessionStart`
injection — pull rather than push.
