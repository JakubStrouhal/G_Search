---
description: Read the critical files and report where the work stands. YAML only.
argument-hint: [bug]  (optional — default reads the deliverable files)
allowed-tools: Bash(git:*), Read, Grep, Glob
disable-model-invocation: true
---

Prime context: $ARGUMENTS

`CLAUDE.md` is already loaded, and the `SessionStart` hook already printed the branch,
the last commits, `git status`, `INDEX.md`'s *Now / Next* and the *Decisions* buffer.
Don't repeat any of it.

## Default

Read, in order:

1. `INDEX.md` — Board, Pending, Known issues
2. `docs/analysis/FINDINGS.md` — the tagged claims
3. The `SPEC.md` of the highest-numbered `docs/analysis/<nnn>-<slug>/` folder — what is
   approved to build and what its decision log settled

Read `docs/analysis/PLAN.md` only if the task needs the F1–F6 taxonomy or the live
reconnaissance.

```yaml
mode: general
board: {A: <status>, B: <status>, C: <status>}
blocking:
  - <what is blocked, and by what>
hazards:                    # INDEX.md Known issues, live ones only
  - <n>: <short>
next: <the one thing>
```

## `bug`

Debugging what another agent did on this branch. Run `git log main..HEAD --oneline`,
`git diff main --stat`, `git diff main --name-only`.

```yaml
mode: bug
commits: [<hash: subject>]
files: {modified: [], added: [], deleted: []}
stats: {files: <n>, +<n>, -<n>}
key_areas:
  - <short>
```

## Rule

Output the YAML block and nothing else. Unknown is `unknown`, never a guess — this repo
is graded on whether claims survive checking.
