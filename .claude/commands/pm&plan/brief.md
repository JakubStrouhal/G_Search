---
description: Open a unit of work — create docs/analysis/<nnn>-<slug>/BRIEF.md stating the question and what would change the answer.
argument-hint: <slug>  (short kebab-case, e.g. part-c-writeup)
allowed-tools: Bash(ls:*), Bash(git:*), Read, Grep, Glob, Write, Edit
disable-model-invocation: true
---

Open a unit of work: $ARGUMENTS

## 1. Number the folder

```bash
ls docs/analysis | grep -E '^[0-9]{3}-' | sort | tail -1
```

Next number, zero-padded: `docs/analysis/<nnn>-<slug>/`. If a folder for this slug already exists,
**stop and say so** — reopening an existing unit of work is an edit, not a new brief.

## 2. Read before writing

`INDEX.md` (board, pending, known issues) and `docs/analysis/FINDINGS.md`. Read
`docs/analysis/PLAN.md` only if the work touches the F1–F6 taxonomy.

A brief that restates what those files already say is waste. The brief's job is the *question*.

## 3. Write `BRIEF.md`

```markdown
---
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
note: One sentence — what changed and why. Overwritten in place, never appended.
---

# <title>

Opened <YYYY-MM-DD>.

## The question
One paragraph. What do we not currently know, or what do we not currently have?

## Why now
What in INDEX.md or FINDINGS.md makes this the next thing. Link the pending item if there is one.

## What would change the answer
The facts that, if they came back differently, would make this work unnecessary or point it
somewhere else. **Check these first** — if one already resolves it, close the brief and say so.

## Constraints
Time budget. What must stay true (the brief's grading criteria, existing contracts like
`outputs/query_classes.csv`). What is explicitly out of scope.

## Done looks like
The artifact this produces, and how someone would tell it worked.
```

Both dates are today's, and `note` says in one sentence what this brief opens and why.
`.claude/hooks/unit-frontmatter.sh` maintains `updated` afterwards; it cannot author `note`.

## 4. Rules

- **No numbers that are not in `FINDINGS.md`.** If you need a new one, run the script and put it in
  `FINDINGS.md` first. A brief is not a place for a number to be born.
- **Unknown is `unknown`.** This repo is graded on whether claims survive checking.
- If answering "what would change the answer" makes the work unnecessary, **say that and stop.**
  That is the highest-value outcome this command has.

## 5. Decision row

Append one row to `INDEX.md`'s Decisions table per `.claude/decision-row.md` — only if opening this
brief *decided* something (a direction chosen, an alternative rejected). Opening work that was
already queued in Pending is not a decision.

## 6. Report, ≤4 lines

Folder created · the question in one sentence · what would change the answer · whether anything in
step 4 argues against doing it at all.
