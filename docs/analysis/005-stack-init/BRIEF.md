# Stack init — connect Supabase, scaffold the app, create no schema

Opened 2026-08-06. Plan only; nothing below has been executed.

## The question

SPEC §10 step 1 is "Supabase project + migrations + seeds". The owner's instruction splits it: do
the **project** half now — a local Supabase stack, a linked remote project, a Vue 3 app that can
talk to it — and **create no database yet**. So: what is the smallest set of changes that leaves
this repo able to run `npx supabase db reset` and `npm run dev` successfully, with **zero migration
files and zero tables**, and with every decision the schema will later depend on written down
rather than inherited by accident?

Scope reading, stated so it can be checked: *no schema* means no files under
`supabase/migrations/`, no `pgvector`, no seeds, no `gen types`. It does **not** exclude
`supabase init` (which only writes `config.toml`) or booting an empty local stack.

## Why now

INDEX.md Now/Next ranks "Build Part B" first and records **zero lines built**. Pending 4.1 is "the
entire remaining risk". This unit takes the stage-setting half of build-order step 1 off that risk
without touching step 4 (the threshold sweep), which gates all UI work.

## What would change the answer

Checked before writing:

- **Does a remote Supabase project already exist?** No evidence in the repo — no `.env`, no
  `supabase/` directory, no `.temp/project-ref`. **Treated as unknown.** Step 5 is gated on the
  owner supplying a project ref; everything else is local-first and proceeds without it.
- **Is `web/` empty?** No. `web/mock/` holds `build.py`, `states.html`, `README.md` and is the
  artifact that settles the design decisions in `docs/design/DESIGN-SYSTEM.md` §8. A scaffolder run
  at `web/` would collide with it. Drives decision A below.
- **Is the CLI present?** Yes — `npx supabase --version` → 2.111.0. Node v22.16.0, npm 10.9.2.

## Constraints

- **Budget: ~1.5–2 h.** This is plumbing. SPEC §6 already concedes the build is 15–20 h against a
  3–5 h phase budget; this unit must not spend more of it than it has to. Log real hours.
- **No schema.** The acceptance test is deliberately "boots clean with nothing in it".
- **No UI beyond a skeleton.** SPEC §10 step 4 gates the F1–F6 screens. A route shell and a health
  check are in scope; a search box is not.
- **`web/mock/` must keep working** — `python3 web/mock/build.py` still rebuilds `states.html`.
- **`docs/brief/` stays immutable.** Nothing written here reads from it yet anyway.
- Out of scope: migrations, seeds, embeddings, RPC, Vercel, CI, the MCP server.

## Decisions to record now, not inherit

These are the ones that get made silently and wrongly if the plan doesn't name them.

**A. Where the Vue app lives → `web/app/`.** `web/mock/` stays where it is; its README's commands
keep working. CLAUDE.md's "`web/` Vue 3 front end" line becomes "`web/app/`" and needs the edit.
The alternative — scaffold in place and preserve `mock/` by hand — buys nothing and risks the
scaffolder clobbering files.

**B. Design tokens are imported, not forked.** `web/mock/build.py` inlines
`docs/design/outputs/tokens.css` and `docs/design/assets/prototype-theme.css`. The Vue app imports
those same two files. A second copy of the token values would drift from the mock within a day.

**C. Seeds will be generated, never hand-typed.** The Supabase playbook says "seed data lives
inside migrations"; CLAUDE.md says "seed the DB from `docs/analysis/outputs/` — never hand-type a
number into a migration". Both hold if the **generator script is the committed artifact and the
seed migration is its output**. Recorded here so the next session does not paste hand-written
`INSERT`s out of the playbook. Nothing is built for it in this unit.

**D. RLS posture: `anon` read, no `anon` write except `demand_events`.** A grader clicks without
logging in, so `authenticated`-only policies would break the demo. That is a deliberate trade for a
demo environment, not a default copied from another repo — it gets stated in Part C's honesty
register. No policy is written in this unit; the posture is fixed so the first schema migration
doesn't have to re-decide it.

**E. Local is the default target; remote needs per-run approval.** All development against the
local stack. `db push` and any mutating SQL against the remote project require the owner naming
prod in the instruction, every run.

**F. The browser gets the publishable key, not the legacy `anon` key.** Added 2026-08-06 after
installing Supabase's own agent skills (`.claude/skills/supabase/`), which state plainly that anon
keys are compatibility-only. Costs nothing now; would be a find-and-replace across the FE later.
The service-role/secret key is never written to a file in this repo — it is read from
`npx supabase status` at the moment it is needed.

**G. Schema workflow — imperative migrations.** Owner's call, 2026-08-06. Declarative
(`supabase/schemas/`) reads better as a schema grows, but it costs a workflow this repo has not
used and seed data would need its own migration anyway; against the stated budget tension that
does not pay. The skill's iterate-then-commit loop still applies: change the local DB with
`supabase db query`, then `supabase db pull <name> --local` to generate a reviewed migration —
**never** `apply_migration`, which burns a history entry per call and poisons subsequent diffs.

**I. Remote link deferred.** Owner's call, 2026-08-06: stay local. Schema, embeddings, the
threshold sweep and the UI are all built and verified against the local stack. The link happens
when it is time to host for the grader (pending 4.4 / 8.2), and nothing before then depends on it.

**H. Three RLS traps the schema unit must not walk into** — from the same skill, all relevant to
SPEC §6's "SQL views, RPC, RLS" backend:
- **Views bypass RLS by default.** Any view needs `WITH (security_invoker = true)` on PG 15+.
- **`SECURITY DEFINER` functions in `public` are callable by `anon` by default** — Postgres grants
  `EXECUTE` to `PUBLIC`. The search RPC must be `SECURITY INVOKER` unless there is a stated reason.
- **RLS is not the same as Data API exposure.** A table may need an explicit `GRANT` to `anon`
  *and* RLS enabled. Getting one without the other is either a broken demo or an open database.

## The work — ordered

| # | Step | Output | Gate |
|---|---|---|---|
| 1 | **Harden `.gitignore` first.** Currently four entries, none of them env- or node-shaped. Add `.env`, `.env.*`, `!.env.example`, `node_modules/`, `dist/`, `supabase/.branches/`, `supabase/.temp/`, `.vercel/` | `.gitignore` | Before anything Supabase- or npm-shaped exists. The repo has a large uncommitted tree sitting exactly at this boundary |
| 2 | `npx supabase init` | `supabase/config.toml` only | Pin `[db] major_version`; keep default ports (54321/54322/54323). `[storage] enabled = false` is a **contingency** for the known 409 "vector buckets" start failure, not a default |
| 3 | `npx supabase start` → `npx supabase db reset` | Running local stack, empty DB | **This is the acceptance test.** A reset must succeed against zero migration files |
| 4 | `.env.example` (committed) + `web/app/.env.local` (ignored) | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` from `npx supabase status` | Local keys are fixed dev values, not secrets |
| 5 | ~~Remote link~~ | — | **DEFERRED 2026-08-06 (decision I).** Local-only until hosting. Folds into pending 4.4 |
| 6 | Scaffold Vue 3 + Vite + TS at `web/app/` (decision A) | `web/app/` | `npm run dev` serves; `npm run build` passes `vue-tsc` |
| 7 | Single typed client at `web/app/src/config/supabase.ts` | One `createClient`, exported once | `database.types.ts` is **deferred, not promised** — it cannot be generated before a schema exists. The client is untyped until step 1 of the real build |
| 8 | Health-check route: reads `supabase.auth.getSession()` or a trivial RPC-free ping and renders connected/not-connected | One view | Proves FE→BE wiring with no tables. No search UI |
| 9 | Import the design tokens (decision B) | `main.ts` imports both CSS files | Mock and app render the same variables |
| 10 | `.claude/agents/supabase.md` + `.claude/skills/db-validate/SKILL.md` | Two files | Both dirs are README-only today. The LOCAL/PROD table is **duplicated into both** on purpose — the rule must be unmissable regardless of entry point |
| 11 | Stale-doc sweep | CLAUDE.md, INDEX.md | CLAUDE.md still says "`supabase/` and `web/` are not scaffolded yet" and points `web/` at the Vue app. INDEX.md board row B and one decision row |

## Done looks like

1. `npx supabase db reset` exits 0 with **zero files in `supabase/migrations/`**.
2. `npm --prefix web/app run build` passes.
3. `npm --prefix web/app run dev` serves a page that says whether it reached Supabase.
4. `python3 web/mock/build.py` still rebuilds `states.html` unchanged.
5. `git status` shows no `.env` and no `node_modules`.
6. Decisions A–E are written down here and reflected in CLAUDE.md/INDEX.md.

**Explicitly not done:** any table, any migration, any embedding, any F1–F6 screen. The next unit is
SPEC §10 step 1 proper (schema + generated seeds), and step 4 still gates all UI.

## Before building

Run `/review plan` — the CLAUDE.md gate. It is a `UserPromptExpansion` hook, so it has to come from
the owner's prompt; an agent cannot invoke it.
