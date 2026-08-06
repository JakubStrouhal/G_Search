# Codex operating instructions

## Shared repository guidance

Before doing work in this repository, read and follow [`CLAUDE.md`](CLAUDE.md).
It is the repository's shared CloudMD guidance and defines the product context,
evidence standards, source-of-truth files, data constraints, and working rules.

Do not duplicate those rules here: keep this file as the Codex entry point and
keep `CLAUDE.md` as the common instruction source for every harness.

## Instruction scope

This file applies to the whole repository. When they are added, also read and
follow the closest applicable instruction file in these areas:

- `supabase/` for backend and database work.
- `web/` for frontend work.

More specific instructions refine this file for files in their directory tree.
If they conflict with `CLAUDE.md` on repository-wide product, evidence, or data
integrity rules, stop and surface the conflict rather than silently weakening
the shared guidance.
