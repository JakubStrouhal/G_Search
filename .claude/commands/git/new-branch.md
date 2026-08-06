---
description: Create a new local branch with a conventional name and push it to origin. Creates a branch and nothing else.
argument-hint: <what the branch is for>  (free text — type and slug are inferred)
allowed-tools: Bash(git:*), Bash(date:*)
disable-model-invocation: true
---

Create a branch for: $ARGUMENTS

> **Scope.** This command creates a branch and pushes the pointer. It makes no commit, writes no
> file, and touches no `INDEX.md` row, board or decision. `/wrap` owns commits and state; git owns
> history. Do not extend this command to do either.

## 1. Name it

Format: `{type}/{date}-{slug}`

**Type** — from the description:

| If the description mentions | Use |
|---|---|
| bug, fix, error, issue, broken | `fix` |
| docs, documentation, readme, writeup | `docs` |
| test, testing, validate | `test` |
| refactor, cleanup, chore, restructure, deps, tooling | `chore` |
| anything else | `feat` |

**Date** — run it, do not assume it:

```bash
date +%Y%m%d
```

**Slug** — lowercase, hyphen-separated, concise. `add-vendor-validation`, not
`adding-the-vendor-validation-step`. When the branch is for a unit of work, reusing that folder's
slug (`part-b`, `live-validation`) keeps the two findable together — but do not go detecting
folders; this command does not read `docs/analysis/`.

Examples: `feat/20260806-part-b-scaffold` · `fix/20260806-f5-recoverability` ·
`docs/20260806-part-c-writeup`

## 2. Refuse a collision

```bash
git rev-parse --verify --quiet refs/heads/<name> && echo EXISTS
```

If it exists, **stop and say so.** Switching to an existing branch is not creating one — if that
is what was wanted, say the `git switch` line and let the user run it.

## 3. Create it

```bash
git checkout -b <name>
```

This working tree is normally dirty, and that is fine — **do not add a clean-tree guard, it would
never pass here.** Staged and unstaged changes come across to the new branch, which is usually the
intent. Immediately after switching, run `git status --short` so it is visible *which* in-flight
work now sits on this branch.

## 4. Push the pointer

```bash
git push -u origin <name>
```

This creates a public ref on `origin` (`JakubStrouhal/G_Search`). It publishes no commits — only
the branch pointer at whatever `HEAD` already was. No `origin` configured, or the push is refused →
leave the branch local and say so plainly; the local branch is still a valid outcome.

## 5. Report, ≤4 lines

Branch name · tracking set or local-only · what `git status --short` shows came along · the next
action.
