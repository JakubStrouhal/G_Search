---
description: Turn a BRIEF.md into a buildable SPEC.md in the same folder. Refuses to run without a brief.
argument-hint: [<nnn>-<slug>]  (optional — defaults to the highest-numbered folder with a BRIEF.md and no SPEC.md)
allowed-tools: Bash(ls:*), Bash(python3:*), Bash(git:*), Read, Grep, Glob, Write, Edit
disable-model-invocation: true
---

Specify: $ARGUMENTS

## 1. Find the folder

Default: the highest-numbered `docs/analysis/<nnn>-<slug>/` that has a `BRIEF.md` and no `SPEC.md`.

- **No `BRIEF.md` → stop.** Say "run `/brief <slug>` first" and do nothing else. The question comes
  before the answer; this is the whole point of the pipeline.
- **`SPEC.md` already exists → stop** and ask whether to revise it. Overwriting a spec someone may
  have started building from is not a default.

## 2. Read

`BRIEF.md` in full. Then `INDEX.md`, `docs/analysis/FINDINGS.md`, and whatever the brief points at.

**Re-run the script behind any number you are about to put in the spec.** Numbers in prose drift;
a spec is where a drifted number becomes a built thing.

## 3. Write `SPEC.md`

```markdown
# <title> — spec

Approved to build <YYYY-MM-DD>. Brief: `BRIEF.md` in this folder.

## Thesis
The one sentence this has to prove. If you cannot write it, the brief was not ready.

## Scope — locked
Table: MUST / HIGH / NICE / CUT, each with why. **The CUT rows carry the most weight** — they are
where judgement is visible, and this brief grades honesty about limits.

## Required behaviour
What it does, case by case. Traceable to a finding: if a behaviour cannot be traced to one in
`FINDINGS.md`, it is not in scope.

## What it does when it has no good answer
**Mandatory section — this is the brief's explicit hard requirement.** Not an error page: the
behaviour on the unanswerable cases is a graded deliverable in its own right.

## Architecture
Only the decisions that constrain the build. Not a tour.

## Acceptance criteria
Checkable statements. "The staff panel shows the assigned class and whether the threshold agrees",
not "the staff panel is good".

## Honesty register
What this will not know, will fabricate if careless, or calibrates by hand. Carries into Part C.

## Build order
Numbered. Put whatever could invalidate the plan **first**, before any UI work.

## Decision log
Every open question the brief left, resolved here, with the reason. One row each.
```

## 4. Rules

- **Resolve every open question. A spec with an open decision is a brief.** If one genuinely cannot
  be resolved without building, say which build step resolves it and make that step 1.
- **Prefer the smaller system.** Output-per-hour is graded and more hours is explicitly not a better
  score. If the stack is a 3× overrun on the budget in the brief, that is a finding about the spec.
- **Name what would make the spec wrong.** A spec that cannot fail was not specific.

## 5. Decision row

Append one row per `.claude/decision-row.md` — the single resolution that would most change what
the builder does. The rest live in the spec's own decision log.

## 6. Report, ≤5 lines

Spec path · the thesis · the decisions resolved · the one thing in the build order that gates the
rest · anything the brief asked for that you cut, and why.
