# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is not a software product — it is a take-home case study for **Groupon R29944, Senior Product Manager, AI (Discovery, International)**. The brief is `Context/R29944_Case_Study_—_Senior_PM__AI_Generalist_(Discovery__International).pdf`.

The brief asks for three connected deliverables:

- **Part A — what is broken.** Analysis of the supplied data, with the numbers behind it. "We will run it or check it, so show your working." Deliberately does not say what to look for.
- **Part B — what right looks like.** A *working, clickable prototype* (not a deck, not screenshots). Hard requirement: it must handle **every query type found in Part A, including the ones that cannot be fixed** — "what it does when it has no good answer tells us as much as what it does when it has one." Any tool is allowed (Artifacts, v0, Lovable, hand-written React); authorship of the code is explicitly not assessed.
- **Part C — a writeup, two pages maximum**, covering: what was found with numbers; what was built and why *rather than the other options*; next steps with an engineering team and what is needed from the platform teams who own search globally; how success would be measured in production and what would signal it was not working. Plus **a short log**: hours spent, which AI tools were used for what, and one or two sentences on what the tools got wrong that had to be caught.

Constraints that should shape every decision here:

- **No clarifying questions are answered.** Handling an underspecified brief is part of the exercise — when something is ambiguous, decide, and write down what was decided.
- **Assessed on:** finding what is actually going on rather than the first thing that looks like a finding; whether the prototype reflects the analysis rather than being a nice search UI bolted on beside it; whether claims survive being checked against the data; honesty about the limits of what was built; output per hour.
- **Not assessed on:** production code quality, test coverage, visual design. "Ship the rough thing that works." More hours is explicitly *not* a better score.

## Current state

| Part | Status | Artifact |
|---|---|---|
| A | Substantially done | `Context/validate.py`, `Context/FINDINGS.md` |
| B | Not started | — |
| C | Not started | — |

`PLAN.md` (repo root) holds the decomposition and the phased next-step plan: the
brief's claims with a testability verdict for each, a live reconnaissance pass over
the production Groupon sites, a six-class failure taxonomy (F1–F6) derived from a
supply × system-response grid, and the build/measurement phases. Read it before
starting Part B — the prototype's required behaviours are keyed to the F-classes.

There is no git repo yet. Delivery is a git repo, a zip, or links; a hosted link is preferred for the prototype.

## Commands

```bash
# Part A analysis — MUST be run from Context/, the CSV paths are relative
cd Context && python3 validate.py

# The script is a linear top-to-bottom sequence of LAYER blocks with no CLI args.
# To iterate on one layer, slice the output rather than editing the script:
cd Context && python3 validate.py | sed -n '/LAYER 3 /,/LAYER 4 /p'
```

Environment notes discovered on this machine (macOS, Python 3.14.2 via Homebrew):

- `pandas` 3.0.1 and `numpy` 2.4.2 are installed system-wide and `validate.py` runs clean against them.
- The system Python is PEP 668 managed — `pip install --user` fails. Create a venv for any additional dependency: `python3 -m venv .venv && .venv/bin/pip install <pkg>`.
- There is **no `pdftotext`/poppler and no PDF library installed**. To re-read the brief PDF, install `pypdf` in a venv and use `extract_text(extraction_mode="layout")`. Naive stream extraction produces garbage — the PDF uses Type0/CIDFontType2 fonts with per-glyph text matrices.

## Data model

Both CSVs live in `Context/` and join on `market` + `city`.

- `search_log.csv` — 8,997 rows, June 1–30 2026, 613 unique raw queries. Columns: `query_id, market, city, raw_query, results_shown, clicked, purchased, date`. 5 markets (GB, DE, FR, ES, PL) × 4 cities each.
- `deals.csv` — 568 rows. Columns: `deal_id, market, city, title, category_l1, category_l2, price_usd, rating, num_ratings, is_bookable`. Only **4 L1 / 5 L2 categories** (`activities, beauty, dining, fitness, massage`) and only **15 unique titles per market** (75 total).

**The single most important structural limitation:** `results_shown` is a *count only*. There is no query→deal mapping and no relevance score. Any claim about *which* deals a query returned is inference from the category structure, not observation. The brief is explicitly testing whether that line gets drawn honestly.

Data is synthetic but modelled on real market weights. Deal titles are in local languages; queries are as typed, including in languages that do not match the market.

## Architecture of the analysis

`validate.py` is deliberately structured as numbered layers, each printing its own counts, so that any headline number can be traced back to a line number:

- **Layer 0** — shape and integrity. Nulls, duplicate IDs, market/city agreement across files, funnel-impossible rows (click with zero results, purchase without click). All come back clean, which is itself the evidence that the data is synthetic.
- **Layer 1** — zero-result rate by market/city/week, with Wilson score intervals (`wilson()`). The CI machinery exists to stop per-market storytelling: only PL-worst/DE-best survives non-overlap.
- **Layer 1b** — the distribution of `results_shown`, which is where the headline changes.
- **Layer 2 / 2b** — splits market+query pairs into `always_zero` / `intermittent` / `never_zero`, then tests whether intermittency is a *city* effect. This split is what separates a supply problem from a matching problem.
- **Layer 3 / 3b** — the hand-built `CONCEPTS` keyword map and `CONCEPT_TO_L2`, used to test whether a zero-returning query has stock in a category that would answer it. The map is hand-built on purpose; an LLM-generated one is a fabrication risk that cannot be defended in Part C.
- **Layer 4** — near-miss/typo sizing via `SequenceMatcher`, to kill the typo theory with a number rather than an assertion.
- **Layer 5 / 5b** — funnel baselines, recoverable-demand upper bound (labelled as an upper bound, not a forecast), and supply density vs outcome.

`FINDINGS.md` is the handoff contract from Part A to Parts B and C. It tags every statement **VERIFIED** (came out of the script), **INFERRED** (interpretation), or **CANNOT VERIFY** (a limit of the dataset that must be stated in Part C). Preserve that taxonomy when editing it — it is the mechanism by which claims survive checking.

## The core finding (drives what Part B must be)

The catalogue matches at category level, not item level, which produces three *structurally different* failures. A prototype that only demos better matching has answered a different question than the one asked:

1. **Silent mismatch** — invisible to every zero-result metric. There are zero paintball, crossfit, sushi and bowling deals in the entire catalogue, yet those queries return full result pages at zero-rates statistically indistinguishable from a query the catalogue actually stocks (escape room). Whether users happily substitute or the generator did not model relevance **cannot be distinguished from this file**.
2. **Supply void** — 64.2% of all zero-result searches; 185 pairs that return zero every single time, almost all adrenaline/aerial (helicopter, balloon, skydiving, rafting, supercar). `activities` holds only city tours, escape rooms and karting. **Search cannot fix this** — it is a merchant-acquisition signal.
3. **Intermittent** — 35.8% of zeros; local-language phrasing against generic local-language titles, with a median city-to-city spread of 0.199. The genuinely fixable matching layer.

Headline: 29.3% of searches return zero, but **1–2 results converts like zero** (CTR 10.3% vs 51.7% at 4+), so the defensible headline is **52.5% combined dead-end**. There is a cliff, not a gradient.

## Known issues to carry forward

- **`validate.py` Layer 3 mislabels adrenaline.** `CONCEPT_TO_L2` maps `adrenaline → activities`; because `activities` exists but stocks none of the requested inventory, the decisive table prints "MATCHER FAILURE" where the truth is a supply void. Fix the map before quoting that table. `FINDINGS.md` §3 documents this deliberately — it is also the best available example for the "what the AI tools got wrong" log the brief asks for.
- **The `unmapped` concept bucket is too large** — 3,806 searches / 883 zeros. Several obviously-adrenaline queries (`paracaidismo`, `paseo en globo`, `vol en montgolfiere`, `lot balonem`, `skoki spadochronowe`, `lot helikopterem`) sit in it; mapping them moves the adrenaline share *up* from 47.6%.
- **Two different typo numbers exist and mean different things.** `FINDINGS.md` §4 quotes 198 zeros / 7.5% (all pairs with n ≤ 3); Layer 4's near-miss test prints 51 / 1.9%. Both reproduce. Say which definition is being used.
- **`FINDINGS.md` §5 funnel figures have drifted** (38.4/30.0/11.5 vs the script's current 38.1/29.8/11.4). Re-run `validate.py` before quoting any number, as the file itself instructs.
- **No search anywhere returns exactly 3 results** — the distribution runs 0, 1, 2, then jumps to 4. Ranking cut-off or generator artifact; cannot be told apart from this file. The brief rewards noticing it and saying so.
