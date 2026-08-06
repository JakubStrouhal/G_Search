# CLAUDE.md

## What this repository is

A **software product** — a Supabase + Vue 3 discovery application — built as the deliverable for a
take-home case study: **Groupon R29944, Senior Product Manager, AI (Discovery, International)**. The
brief is `docs/brief/R29944_Case_Study_—_Senior_PM__AI_Generalist_(Discovery__International).pdf`.

Both halves matter. It is a real DB–BE–FE application, so build it like one. It is also graded
against the brief below, and the brief does **not** grade code quality, test coverage or visual
design — it grades whether the product reflects the analysis and whether the claims survive
checking. Where the two pull apart, the brief wins.

Three connected deliverables:

- **Part A — what is broken.** Analysis of the supplied data with the numbers behind it. "We will
  run it or check it, so show your working." Deliberately does not say what to look for.
- **Part B — what right looks like.** A *working, clickable prototype* — not a deck, not
  screenshots. Hard requirement: it must handle **every query type found in Part A, including the
  ones that cannot be fixed**. "What it does when it has no good answer tells us as much as what it
  does when it has one." Any tool allowed; authorship of the code is explicitly not assessed.
- **Part C — a writeup, two pages max.** What was found with numbers; what was built and why
  *rather than the other options*; next steps with an engineering team and what is needed from the
  platform teams who own search globally; how success would be measured and what would signal it
  was not working. Plus **a short log**: hours spent, which AI tools were used for what, and one or
  two sentences on what the tools got wrong that had to be caught.

Constraints that shape every decision:

- **No clarifying questions are answered.** Handling an underspecified brief is part of the
  exercise — when something is ambiguous, decide, and write down what was decided.
- **Assessed on:** finding what is actually going on rather than the first thing that looks like a
  finding; whether the prototype reflects the analysis rather than being a nice search UI bolted on
  beside it; whether claims survive being checked against the data; honesty about the limits of
  what was built; output per hour.
- **Not assessed on:** production code quality, test coverage, visual design. "Ship the rough thing
  that works." More hours is explicitly *not* a better score.

## Status lives in one place

**`INDEX.md` is authoritative for status, the work queue and known defects.** This file states none
of them on purpose — a second copy is a copy that drifts. The `SessionStart` hook injects INDEX's
*Now / Next* and *Decisions* blocks at startup, so you are already oriented; `/prime` reads deeper
when a session is about to do real work.

## Repo layout

```
docs/brief/       Exactly what Groupon supplied — the PDF and the two CSVs.
                  Immutable input; nothing writes back to it.
docs/analysis/    The work: FINDINGS.md, PLAN.md, the scripts, outputs/.
docs/analysis/outputs/     Generated CSVs. Regenerable, never hand-edited.
docs/analysis/<nnn>-<slug>/    One folder per unit of work: BRIEF.md -> SPEC.md -> RESULT.md.
docs/chores/      One flat file per chore, written by `/chore`. Maintenance only — no claims.
supabase/         Migrations, seeds, RPC. The DB and BE layer. `config.toml` only so far.
web/app/          Vue 3 + Vite + TS front end.
web/mock/         Static state gallery that settled the design decisions. Not the app.
INDEX.md          State: board, queue, known defects, last 6 decisions.
README.md         Grader entry point.
```

**Both are scaffolded and empty on purpose** (`005-stack-init`): the local Supabase stack boots with
**zero migrations and zero tables**, and `web/app` is a Vue shell whose only screen is a Supabase
health check. The approved build spec is `docs/analysis/001-part-b/SPEC.md` — read §6 (architecture)
and §10 (build order) before adding to either. **Build-order step 4 (the threshold sweep) gates all
UI work**, so do not add screens ahead of it.

Schema workflow is **imperative migrations**, not declarative. Iterate on the local DB with
`supabase db query`, then `supabase db pull <name> --local` to generate one reviewed migration.
Never `apply_migration` — it writes a history entry per call and poisons later diffs. Supabase's own
agent skills are installed at `.claude/skills/supabase*/`; read them before touching schema or RLS.

`docs/analysis/FINDINGS.md` is the Part A → B/C handoff contract. Every statement is tagged
**VERIFIED** (came out of a script), **INFERRED** (interpretation) or **CANNOT VERIFY** (a limit of
the dataset that must be stated in Part C). Preserve that taxonomy when editing — it is the
mechanism by which claims survive checking.

## Data model

Both CSVs live in `docs/brief/` and join on `market` + `city`.

- `search_log.csv` — 8,997 rows, June 1–30 2026, 613 unique raw queries. Columns:
  `query_id, market, city, raw_query, results_shown, clicked, purchased, date`. 5 markets
  (GB, DE, FR, ES, PL) × 4 cities each.
- `deals.csv` — 568 rows. Columns: `deal_id, market, city, title, category_l1, category_l2,
  price_usd, rating, num_ratings, is_bookable`. Only 4 L1 / 5 L2 categories (`activities, beauty,
  dining, fitness, massage`) and only 15 unique titles per market (75 total).

**The single most important structural limitation:** `results_shown` is a *count only*. There is no
query→deal mapping and no relevance score. **Any claim about *which* deals a query returned is
inference from the catalogue, not observation.** The brief is explicitly testing whether that line
gets drawn honestly — do not invent the join.

Corollary, learned the hard way: test whether stock exists at **title level**, not `category_l2`
level. There are only five L2 categories, so a category-level test reports "the category exists"
for concepts the catalogue stocks nothing for.

Data is synthetic but modelled on real market weights. Deal titles are in local languages; queries
are as typed, including in languages that do not match the market.

## Commands

```bash
# Part A analysis — runs from anywhere; paths resolve against the script file
python3 docs/analysis/validate.py       # Layers 0-5b: shape, zero-rates, always/intermittent
                                        # split, concept-coverage, typo sizing, funnel. stdout only
python3 docs/analysis/classify.py       # F1-F6 classifier -> outputs/query_classes.csv, fix_list.csv
python3 docs/analysis/language_test.py  # matched-pair language test -> outputs/language_pairs.csv

# Each script is a linear sequence of blocks with no CLI args. To iterate on one, slice the
# output rather than editing the script:
python3 docs/analysis/validate.py | sed -n '/LAYER 3 /,/LAYER 4 /p'

# Live search probe — docs/analysis/live_probe.js is NOT run with node. Paste it into the
# DevTools console on a groupon.co.uk / groupon.pl page, then:
#   await probeGB()  |  await probePL()  |  await probeSuggest()
# It replays Groupon's own persisted GraphQL query to read exact result counts; the UI only
# shows buckets ("400+"), which is not precise enough to reason from.

# Notebooks — need the venv (scipy/matplotlib/jupyter are NOT system-wide)
python3 -m venv .venv && .venv/bin/pip install pandas numpy scipy matplotlib jupytext jupyter
.venv/bin/python docs/analysis/002-recoverability/notebook.py     # runs as a plain script

# The .py with `# %%` markers is the source of truth — it diffs in git. The .ipynb and the
# shareable HTML are generated from it, never hand-edited:
.venv/bin/jupytext --to ipynb --execute docs/analysis/002-recoverability/notebook.py \
  -o docs/analysis/002-recoverability/notebook.ipynb
.venv/bin/jupyter nbconvert --to html --embed-images \
  docs/analysis/002-recoverability/notebook.ipynb \
  --output-dir docs/analysis/002-recoverability/outputs
```

### Independent review gate

Before committing to a plan, material refinement, or a claim that a change works, run Claude's
`/review` command:

```text
/review plan [optional focus]
/review refine [optional focus]
/review test [optional focus]
```

It invokes a separate Codex process through Claude's `UserPromptExpansion` hook. Codex is
read-only and ephemeral; it is an independent interviewer, not an implementer. Claude must verify
its findings against the repository and return a Proceed / Proceed with changes / Stop disposition.
An unavailable reviewer is unknown, never a pass. Details live in `.claude/hooks/README.md`.

`validate.py` and `classify.py` each carry their **own hand-built `CONCEPTS` map**. They are
independent and can drift from each other — check both if you change either. The maps are
hand-built on purpose: an LLM-generated one is a fabrication risk that cannot be defended in Part C.

### The application

```bash
# DB / BE — Supabase (CLI 2.111 present)
npx supabase start                      # local stack; Postgres + Studio
npx supabase db reset                   # re-apply migrations + seeds from scratch
npx supabase migration new <name>       # never hand-edit an applied migration

# FE — Vue 3 + Vite + TS (node 22.16, npm 10.9 present)
npm --prefix web/app run dev            # http://localhost:5173
npm --prefix web/app run build          # vue-tsc -b && vite build — type errors fail the build
```

Env lives in `web/app/.env.local` (gitignored); `.env.example` at the repo root is the template.
The browser gets `VITE_SUPABASE_PUBLISHABLE_KEY`, **not** the legacy anon key and never the secret
key. Design tokens are imported from `docs/design/` via the `@design` alias — the same two files
`web/mock/build.py` inlines, so app and mock cannot drift. The alias is declared **twice**, in
`vite.config.ts` and `tsconfig.app.json`; edit both or resolution breaks in one of them silently.

**Keys and model calls live in the BE, never in the browser.** Embeddings are precomputed offline
and loaded into Postgres — no model latency while a grader clicks. The front end reads; the only
write path is `demand_events`.

`docs/brief/*.csv` are the seed source. Regenerate `docs/analysis/outputs/` from the scripts, and
seed the DB from those outputs — never hand-type a number into a migration.

## Environment (macOS, Python 3.14.2 via Homebrew)

- `pandas` 3.0.1 and `numpy` 2.4.2 are installed system-wide; the scripts run clean against them.
- `scipy` and `matplotlib` are **not** installed. `ipykernel` is.
- System Python is PEP 668 managed — `pip install --user` fails. Use a venv:
  `python3 -m venv .venv && .venv/bin/pip install <pkg>`.
- **No `pdftotext`/poppler and no PDF library.** To re-read the brief, install `pypdf` in a venv and
  use `extract_text(extraction_mode="layout")`. Naive stream extraction produces garbage — the PDF
  uses Type0/CIDFontType2 fonts with per-glyph text matrices.

## Working rules

- **Re-run the script before quoting any number.** Numbers in prose drift; scripts do not.
- **Findings are not status.** A number, a corrected claim or a killed hypothesis goes in
  `FINDINGS.md`. `INDEX.md` records only that it happened.
- **History is git.** Do not hand-maintain a work log.
