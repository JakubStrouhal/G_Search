---
description: Plan a chore — write docs/chores/<slug>.md with the files, the steps and the check. Plans only; does not do the work.
argument-hint: <what the chore is>  (e.g. delete the superseded 001-part-b/archive folder)
allowed-tools: Bash(ls:*), Bash(git:*), Read, Grep, Glob, Write, Edit
disable-model-invocation: true
---

Plan a chore: $ARGUMENTS

A chore is maintenance — deleting dead files, fixing a stale path, tidying a script, scaffolding
config. It changes no claim and answers no question, which is why it skips `/brief` → `/spec` →
`/implement`. **This command writes the plan. It does not do the work.**

## 1. Stop if it is not a chore

Read `INDEX.md` — Known issues and Pending — before anything else.

- **Already listed there?** Cite the number (`Known issue #5`) instead of restating it. A second
  copy of a defect description is a copy that drifts.
- **Touches `docs/analysis/FINDINGS.md` numbers, either `CONCEPTS` map, or an approved `SPEC.md`?**
  Stop. Say "this is not a chore — run `/brief <slug>`." That pipeline is what keeps claims
  checkable; routing around it is the one failure mode this command has.

## 2. Write `docs/chores/<slug>.md`

Short kebab-case slug from the chore itself. If the file exists, stop and say so.

```markdown
# Chore: <name>

Planned <YYYY-MM-DD>.

## What and why
Two or three sentences. What is wrong now, what is true after. Link the `INDEX.md` row if there is
one.

## Files
Each file that changes, and in one clause why. New files under a `### New files` heading.

## Steps
Numbered, in order, shared/foundational first. Each step is something a person can do without
re-deriving the plan.

## Check
How to tell it worked. See rule below.

## Notes
Optional. Anything the person doing it would otherwise have to rediscover.
```

## 3. The check must be real

`web/` and `supabase/` are **not scaffolded** and there is no test suite. Do not write
`npm test`, `npm run build` or `npm run test:e2e` unless you have confirmed the script exists.

List only commands that exist **today** and actually exercise this chore — usually one of
`python3 docs/analysis/validate.py`, `classify.py`, `language_test.py`, or a `git status` / `ls`
that shows the change landed. If nothing automated covers it, write **"no automated check"** and
give the manual one. A plan listing commands that error is worse than a plan admitting there is no
test.

## 4. No `INDEX.md` edit, no decision row

Deliberate. A chore decides nothing and adds no status; `git log` records that it happened. The
exception is when the chore *closes* a Known issue — then say so in the plan's Notes, and let
`/wrap` flip the row.

## 5. Report, ≤4 lines

Path to the plan · what it changes in one sentence · the check · anything in step 1 that argues it
should be a `/brief` instead.
