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
---
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
note: One sentence — what changed and why. Overwritten in place, never appended.
---

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

Both dates are today's, and `note` says in one sentence what this build changed and why.
`.claude/hooks/unit-frontmatter.sh` maintains `updated` afterwards; it cannot author `note`.

## 6. Update `INDEX.md`

Flip the Pending rows this closed to ✅, replacing the Note with what was established — a number, a
path, a verdict — not "done". Add any defect the build created to Known issues. Rewrite the
`state:start` block if the phase moved.

## 7. Decision row

Append one row per `.claude/decision-row.md` — **only if building decided something the spec did
not**. Executing an approved spec is not a decision; that is what `git log` records.

## 8. Independent validation against the spec

Last step, and it is not optional. This is the **build gate**: a second reader who has the spec and
the diff and no stake in the build having gone well. Its counterpart is the **document gate** —
`/spec` §5 and `/plan-team` §6 run the same script as `refine <doc> <source>` *before* anything is
built, so the spec you are being judged against was itself read by someone independent. Shell out to
the same reviewer the `/review` hook uses, in its build mode:

```bash
bash .claude/hooks/codex-interview.sh implement docs/analysis/<nnn>-<slug>/SPEC.md
```

The script collects the diff itself — `git diff HEAD` plus `git status --short`, because most units
here are still untracked and a build made of new files produces no `git diff` at all. Codex is
read-only and ephemeral: it validates, it does not implement. Its last line is
`VERDICT: MATCHES SPEC | DEVIATES | CANNOT TELL`.

Exit status is the part that matters:

| Exit | Meaning | What to do |
|---|---|---|
| 0 | Codex ran; the report is its verdict | Verify each material finding against the repo yourself, exactly as under `/review`. Codex saying it is not evidence. |
| 2 | Bad mode, or no spec at that path | Fix the path and re-run. Do not skip. |
| 3 | Codex did not complete | Report **"spec conformance unvalidated — reviewer unavailable"**. Never a pass. |

**An unavailable reviewer is unknown, not approval.** If the exit status is 3, or the report says
Codex did not complete, say so in the report in those words and do not present the build as
validated against its spec. If the verdict is `DEVIATES` or `CANNOT TELL`, name the deviation and
reconsider any `INDEX.md` row you flipped to ✅ in step 6 — a row marked done on a build that does
not match its spec is exactly the drift this pipeline exists to prevent.

## 9. Report, ≤6 lines

What runs · what does not · what is unverified · **Codex's verdict, or that it was unavailable** ·
where the spec was wrong · the next action.

> Half-done is reported as half-done. A build reported as working that has not been run is the one
> failure this repo cannot afford — it is graded on whether claims survive checking.
