# CLAUDE.md

## What this repository is

A **software product** — a Supabase + Vue 3 discovery application — built as the deliverable for a
take-home case study: **Groupon R29944, Senior Product Manager, AI (Discovery, International)**. The
brief is `docs/brief/R29944_Case_Study_—_Senior_PM__AI_Generalist_(Discovery__International).pdf`.

Both halves matter. It is a real DB–BE–FE application, so build it like one — but the brief grades
whether the product reflects the analysis and whether the claims survive checking, so where building
it well and the brief pull apart, the brief wins. Three connected deliverables:

- **Part A — what is broken.** Analysis of the supplied data with the numbers behind it. "We will
  run it or check it, so show your working." The brief does not say what to look for.
- **Part B — what right looks like.** A *working, clickable prototype*, not a deck. It must handle
  **every query type found in Part A, including the ones that cannot be fixed** — "what it does when
  it has no good answer tells us as much as what it does when it has one." Any tool allowed;
  authorship of the code is explicitly not assessed.
- **Part C — a writeup, two pages max.** What was found with numbers; what was built and why
  *rather than the other options*; next steps with engineering and what the platform teams who own
  search globally must supply; how success is measured and what would signal it was not working.
  Plus **a log**: hours, which AI tools did what, and what they got wrong that had to be caught.

Constraints: **no clarifying questions are answered** — when something is ambiguous, decide and
write down what was decided. **Assessed on** finding what is actually going on rather than the first
thing that looks like a finding; whether the prototype reflects the analysis rather than being a
nice search UI bolted on beside it; whether claims survive checking; honesty about the limits of
what was built; output per hour. **Not assessed on** code quality, tests or visual design — "ship
the rough thing that works", and more hours is explicitly *not* a better score.

## Status lives in one place

**`INDEX.md` is authoritative for status, the work queue and known defects.** This file states none
of them on purpose — a second copy is a copy that drifts. The `SessionStart` hook injects INDEX's
*Now / Next* and *Decisions* blocks at startup, so you are already oriented; `/prime` reads deeper
when a session is about to do real work.

The repo layout is documented once, in `README.md` § Layout. The approved build spec for Part B is
`docs/analysis/001-part-b/SPEC.md` — read §6 (architecture) and §10 (build order) before adding to
`supabase/` or `web/app/`. `docs/analysis/FINDINGS.md` is the Part A → B/C handoff contract: every
statement is tagged **VERIFIED**, **INFERRED** or **CANNOT VERIFY**. Preserve that taxonomy when
editing — it is the mechanism by which claims survive checking.

## Data model

Both CSVs live in `docs/brief/` and join on `market` + `city`. Row counts and date range live in
`FINDINGS.md` §0, category shape and the L1/L2 names in §3 and §8; do not restate them here.

- `search_log.csv` — `query_id, market, city, raw_query, results_shown, clicked, purchased, date`.
- `deals.csv` — `deal_id, market, city, title, category_l1, category_l2, price_usd, rating,
  num_ratings, is_bookable`.

**The single most important structural limitation:** `results_shown` is a *count only*. There is no
query→deal mapping and no relevance score. **Any claim about *which* deals a query returned is
inference from the catalogue, not observation.** The brief is explicitly testing whether that line
gets drawn honestly — do not invent the join.

Corollary, learned the hard way: test whether stock exists at **title level**, not `category_l2`
level. There are only five L2 categories, so a category-level test reports "the category exists"
for concepts the catalogue stocks nothing for.

`validate.py` and `classify.py` each carry their **own hand-built `CONCEPTS` map**. They are
independent and can drift from each other — check both if you change either. The maps are
hand-built on purpose: an LLM-generated one is a fabrication risk that cannot be defended in Part C.

Data is synthetic but modelled on real market weights. Deal titles are in local languages; queries
are as typed, including in languages that do not match the market.

## Commands

The Part A scripts, how to slice their output and the live search probe live in `README.md`.

```bash
# Notebooks — need the venv (scipy/matplotlib/jupyter are NOT system-wide). <unit> below is a
# work-unit folder such as docs/analysis/002-recoverability or docs/analysis/004-data-story
python3 -m venv .venv && .venv/bin/pip install pandas numpy scipy matplotlib jupytext jupyter
.venv/bin/python docs/analysis/002-recoverability/notebook.py     # runs as a plain script

# The .py with `# %%` markers is the source of truth — it diffs in git. The .ipynb and the
# shareable HTML are generated from it, never hand-edited:
.venv/bin/jupytext --to ipynb --execute <unit>/notebook.py -o <unit>/notebook.ipynb
.venv/bin/jupyter nbconvert --to html --embed-images <unit>/notebook.ipynb --output-dir <unit>/outputs

# DB / BE — Supabase (CLI 2.111 present)
npx supabase start                      # local stack; Postgres + Studio
npx supabase db reset                   # re-apply migrations + seeds from scratch
npx supabase migration new <name>       # never hand-edit an applied migration

# FE — Vue 3 + Vite + TS (node 22.16, npm 10.9 present)
npm --prefix web/app run dev            # http://localhost:5173
npm --prefix web/app run build          # vue-tsc -b && vite build — type errors fail the build
```

### Schema

Imperative migrations, **not** declarative. Iterate on the local DB with `supabase db query`, then
`supabase db pull <name> --local` to generate one reviewed migration. **Never `apply_migration`** —
it writes a history entry per call and poisons later diffs. Supabase's own agent skills are
installed at `.claude/skills/supabase*/`; read them before touching schema or RLS.

`docs/brief/*.csv` are the seed source. Regenerate `docs/analysis/outputs/` from the scripts and
seed the DB from those outputs — never hand-type a number into a migration.

### The application

Env lives in `web/app/.env.local` (gitignored); `.env.example` at the repo root is the template. The
browser gets `VITE_SUPABASE_PUBLISHABLE_KEY`, **not** the legacy anon key and never the secret key.
**Keys and model calls live in the BE, never in the browser.** Embeddings are precomputed offline
and loaded into Postgres — no model latency while a grader clicks. The front end reads; the only
write path is `demand_events`.

Design tokens are imported from `docs/design/` via the `@design` alias — the same two files
`web/mock/build.py` inlines, so app and mock cannot drift. The alias is declared **twice**, in
`vite.config.ts` and `tsconfig.app.json`; edit both or resolution breaks in one of them silently.

## Environment (macOS, Python 3.14.2 via Homebrew)

- `pandas` 3.0.1 and `numpy` 2.4.2 are installed system-wide and the scripts run clean against them;
  `ipykernel` is installed; `scipy` and `matplotlib` are **not**.
- System Python is PEP 668 managed — `pip install --user` fails. Use a venv (see Commands).
- **No `pdftotext`/poppler and no PDF library.** To re-read the brief, install `pypdf` in a venv and
  use `extract_text(extraction_mode="layout")`. Naive stream extraction produces garbage — the PDF
  uses Type0/CIDFontType2 fonts with per-glyph text matrices.

## Working rules

- **Re-run the script before quoting any number.** Numbers in prose drift; scripts do not.
- **History is git.** Do not hand-maintain a work log.
- **The Codex reviewer runs at two gates, one per half of the pipeline, plus on request — never as a
  routine pass over the tree.** Both gates shell out to `.claude/hooks/codex-interview.sh`, which is
  read-only and ephemeral: it judges, it never implements.
  - **The document gate — before anything is built.** `/spec` §5 and `/plan-team` §6 run
    `refine <doc> <source>`: `SPEC.md` against its `BRIEF.md`, `PLAN-TEAM.md` against its `SPEC.md`.
    It asks whether the document answers its source and names the gaps, technical and in the
    reasoning. Verdict: `READY TO BUILD | GAPS | NOT READY`. Fix accepted gaps **in the document
    before reporting**; `NOT READY` means the spec is not presented as approved.
  - **The build gate — after the builders are finished.** `/execute:implement` §8 and
    `/execute:team` §6 run `implement <SPEC path>` against the diff. Verdict:
    `MATCHES SPEC | DEVIATES | CANNOT TELL`.
  - **On request:** `/review <plan|refine|test> [focus]`, user-invoked only
    (`disable-model-invocation`), takes no path and challenges the current direction.

  Nothing else triggers it — not an ordinary commit, not a refactor, not a doc edit. Verify its
  findings against the repository yourself and return a Proceed / Proceed with changes / Stop
  disposition. **Exit 3 is an unavailable reviewer, which is unknown, never a pass** — including
  when the operator kill switch `.claude/codex-review.disabled` is in place. That file is gitignored,
  so check whether it exists rather than assuming either way; while it does, no gate has actually run.
