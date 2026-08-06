---
description: Build what SPEC.md specifies — spawns the build agent, writes RESULT.md. Refuses to run without a spec.
argument-hint: [<nnn>-<slug>]  (optional — defaults to the highest-numbered folder with a SPEC.md)
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, Agent, Task
disable-model-invocation: true
---

Implement: $ARGUMENTS

## 1. Find the folder

Default: the highest-numbered `docs/analysis/<nnn>-<slug>/` containing a `SPEC.md`.

**No `SPEC.md` → stop.** Say "run `/spec` first" and do nothing else. Do not infer a spec from the
brief, from `INDEX.md`, or from the conversation. Building from an unwritten spec is how the wrong
thing gets built confidently — which is the failure this pipeline exists to prevent.

If `SPEC.md` carries a "do not build" banner or an unresolved decision, **stop and name it.**

## 2. Read the spec in full, then the gate

Read `SPEC.md` completely before doing anything. Then find its build-order step 1 — the spec is
required to put whatever could invalidate the plan first.

**Run that step yourself, before spawning anything.** If it fails, the spec is wrong and the build
does not start. Report that; it is a successful outcome for this command.

## 3. Spawn the build

Give the agent the spec **path**, not a summary — a summarised spec is a spec that lost its CUT
list. Tell it:

- Read `SPEC.md` in full first, and `docs/analysis/FINDINGS.md` for the findings behind it.
- Build in the spec's build order. Do not reorder to do the visible parts first.
- **Honour the CUT list.** Anything cut stays cut; scope added back is scope nobody approved.
- **Fabricate nothing.** If a number, a mapping or a description is not in the data or the spec,
  it does not go in. Where the data cannot answer, the honest empty state *is* the feature.
- Report what was built, what was skipped, and what is unverified — separately.

Parallelise only across parts of the spec that do not share files.

## 4. Verify before believing it

Run the thing. Exercise the spec's acceptance criteria and its demo cases yourself. An agent
reporting success is not evidence; output is.

## 5. Write `RESULT.md` beside the spec

```markdown
# <title> — result

Built <YYYY-MM-DD>. Spec: `SPEC.md` in this folder.

## What was built
Against each MUST/HIGH in the spec's scope table: done / partial / not done.

## What was skipped, and why
Including anything the spec asked for that turned out to be wrong or impossible.

## What is unverified
Anything not exercised. Say it plainly — this is graded.

## Where the spec was wrong
What building it taught that specifying it did not.

## Hours
The brief requires a log: hours, AI tools used for what, and what they got wrong that you caught.
```

## 6. Update `INDEX.md`

Flip the Pending rows this closed to ✅, replacing the Note with what was established — a number, a
path, a verdict — not "done". Add any defect the build created to Known issues. Rewrite the
`state:start` block if the phase moved.

## 7. Decision row

Append one row per `.claude/decision-row.md` — **only if building decided something the spec did
not**. Executing an approved spec is not a decision; that is what `git log` records.

## 8. Report, ≤6 lines

What runs · what does not · what is unverified · where the spec was wrong · the next action.

> Half-done is reported as half-done. A build reported as working that has not been run is the one
> failure this repo cannot afford — it is graded on whether claims survive checking.
