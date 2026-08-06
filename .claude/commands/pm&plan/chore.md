---
description: Plan a chore — write docs/analysis/<nnn>-<slug>/CHORE.md with the files, the steps and the check. Plans only; does not do the work.
argument-hint: <what the chore is>  (e.g. repoint the commands that still reference deleted .claude files)
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

## 2. Number the folder

Same numbering as `/brief` — a chore is a unit of work, so it lives in the same tree and takes the
next number rather than a parallel one:

```bash
ls docs/analysis | grep -E '^[0-9]{3}-' | sort | tail -1
```

Next number, zero-padded, short kebab-case slug from the chore itself:
`docs/analysis/<nnn>-<slug>/`. If a folder for this slug already exists, **stop and say so.**

## 3. Write `docs/analysis/<nnn>-<slug>/CHORE.md`

`CHORE.md` sits where `BRIEF.md` would. Its presence is what says this unit skipped the pipeline
on purpose; a folder holding both is a contradiction, so if a `BRIEF.md` already exists, stop —
that unit is not a chore.

```markdown
---
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
note: One sentence — what changed and why. Overwritten in place, never appended.
---

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

Both dates are today's, and `note` says what this chore is for in one sentence — write it, do not
leave the template wording. `.claude/hooks/unit-frontmatter.sh` will maintain `updated` from here
on, but it cannot author `note`.

## 4. The check must be real

`web/` and `supabase/` are **not scaffolded** and there is no test suite. Do not write
`npm test`, `npm run build` or `npm run test:e2e` unless you have confirmed the script exists.

List only commands that exist **today** and actually exercise this chore — usually one of
`python3 docs/analysis/validate.py`, `classify.py`, `language_test.py`, or a `git status` / `ls`
that shows the change landed. If nothing automated covers it, write **"no automated check"** and
give the manual one. A plan listing commands that error is worse than a plan admitting there is no
test.

## 5. No `INDEX.md` edit, no decision row

Deliberate. A chore decides nothing and adds no status; `git log` records that it happened. The
exception is when the chore *closes* a Known issue — then say so in the plan's Notes, and let
`/wrap` flip the row.

## 6. Report, ≤4 lines

Path to the plan · what it changes in one sentence · the check · anything in step 1 that argues it
should be a `/brief` instead.
