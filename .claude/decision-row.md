# The decision row — every pipeline command writes one

`/brief`, `/spec`, `/implement` and `/wrap` each append **one row** to the `Decisions` table in
`INDEX.md`, between `<!-- decisions:start -->` and `<!-- decisions:end -->`, as their last step.

**It is a ring buffer, not a log.** **Newest row goes directly under the header; the bottom row is
deleted in the same edit.** The table is exactly six rows plus the header. If it is at six, one
goes out as one comes in. This is the whole design: bounded state does not rot, an append-only log
does — a hand-written one in this repo duplicated itself within a single day, which is why history
is `git log` instead.

| Column | What goes in it | Limit |
|---|---|---|
| Date | Absolute, `YYYY-MM-DD`. Never "today" or "last session". | — |
| Decision | What was *chosen*, in one clause. Not what was done. "Static bundle, not Supabase" — not "wrote the spec". | ≤ 15 words |
| Why | The reason that would stop someone re-opening it. A number, a constraint, a rejected alternative. | **≤ 20 words** |

**The word limits are load-bearing.** The `SessionStart` hook injects the top three rows into every
new session, and the design rule for injected context is that it stays short enough to be read. Row
count alone does not bound size; width does. A long row is a row that costs every future session.

**The buffer is a hand-off aid, not the record.** It tells the next session what was recently
decided and why, then the row falls off. **A decision that must survive belongs in the artifact it
governs** — a spec's decision log, a finding in `FINDINGS.md`. The buffer being full of a single
day's work is normal and does not mean anything was lost.

**Write nothing if nothing was decided.** A command that only executed an existing decision does
not get a row — it would push a real one out of the buffer. Executing is what `git log` is for.

**One row per command run, never more.** If a run made several decisions, write the one that would
most change what the next person does, and put the rest in the artifact itself.
