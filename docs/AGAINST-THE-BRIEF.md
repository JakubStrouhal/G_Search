---
created: 2026-08-07
updated: 2026-08-07
note: Maps every requirement in the Groupon brief to the artifact that answers it and the finding it produced — a traceability sheet, deliberately not a fourth copy of the status or the numbers.
---

# What Groupon asked for, and what exists against it

**Purpose.** One page that answers, requirement by requirement: *what was asked, what was built,
what it found, and what is still missing.* Written to be readable by someone who has not opened the
repository.

**How to read it, and the one rule that keeps it honest.** This file **points**; it does not own
anything. `FINDINGS.md` owns every number and `INDEX.md` owns every status — if this file disagrees
with either, **they win and this is the bug**. Figures appear here only where a claim is unreadable
without them.

**Tags used throughout, carried from `FINDINGS.md`:** **VERIFIED** (a script produced it),
**INFERRED** (interpretation), **CANNOT VERIFY** (a limit of the data, stated rather than resolved).

---

## Part A — "what is broken"

> *Analysis of the supplied data with the numbers behind it. "We will run it or check it, so show
> your working." The brief does not say what to look for.*

**Status: complete, live-validated, and re-spined once.**

| What was built | Where |
|---|---|
| Three analysis scripts, no arguments, pandas + numpy only | `docs/analysis/{validate,classify,language_test}.py` |
| Tagged findings handoff — every claim VERIFIED / INFERRED / CANNOT VERIFY | `docs/analysis/FINDINGS.md` |
| Recoverability simulation with a sensitivity cell | `docs/analysis/002-recoverability/` |
| Pre-registered live probe against production Groupon (P1–P6) | `docs/analysis/003-live-validation/` |
| Business-readable interactive explainer — **now carries chapter 5, the prototype's own result** | `docs/analysis/004-data-story/outputs/explainer.html` |

### What it found

| # | Finding | Tag |
|---|---|---|
| **A1** | **The number a dashboard shows is the wrong number.** 29.3% of searches return zero — but 1–2 results converts like zero (1.7% vs 16.1% search→purchase). The real dead-end rate is **52.5%**, and the cliff survives concept × city stratification, so it is a property of result count, not of which queries land there | VERIFIED |
| **A2** | **When a search failed, where was the answer?** Over all 4,720 dead ends: **nowhere in the market 43.2% · the user's own city 32.2% · another city 3.1% · can't tell 21.5%**. Four buckets, four owners. **Quote the `nowhere` band [43.2%, 64.7%], never one end** | VERIFIED, with a stated band |
| **A3** | **Phrasing costs more than typos do.** English-phrased queries dead-end **81.2%** of the time against **39.0%** for local phrasing — a 42.3pp gap, on matched pairs using only stocked concepts | VERIFIED |
| **A4** | **Most of this is not a search problem.** Search-fixable work is **~12%** of the recoverable opportunity (range 5.6–15.1%) against a supply-void ceiling of +271 purchases/month. F4 is zero by construction, so the *direction* is assumption-free | VERIFIED + a stated assumption set |
| **A5** | **The single most important limit.** `results_shown` is a bare count. There is no query→deal mapping, so **any claim about which deals a query returned is inference, not observation** | CANNOT VERIFY — stated, not resolved |
| **A6** | No search anywhere returns exactly 3 results. Resolved as a **generator artifact**, which withdrew F5's diagnosis and moved the headline from ~18% to ~12% | VERIFIED (live-corroborated) |
| **A7** | **Production Groupon fails the same way, observably.** `skydiving` in London returns 2 deals: an online safety course and a skydive 141.5 miles away. `kitesurf` returns a "Portable Bartender Barista **Kit**" — the matcher matches *fragments*. The API exposes **no relevance score, no matched-term field, no spell-correction field** | VERIFIED (live catalogue only) |

### The honesty boundary, stated up front

**Every number that sizes anything comes from the two supplied CSVs.** One chapter of the explainer
is live production Groupon, probed read-only, and it is visually and verbally quarantined: it shows
*how a real search engine fails* and **sizes nothing**. It earns its place because the brief asks
what the platform teams must supply, and the CSVs contain no information about that.

---

## Part B — "what right looks like"

> *A working, clickable prototype, not a deck. It must handle every query type found in Part A,
> including the ones that cannot be fixed — "what it does when it has no good answer tells us as
> much as what it does when it has one."*

**Status: 4 of 10 build steps done. Backend is real; no UI yet.** Live status is `INDEX.md` 4.1.

| Step | What exists |
|---|---|
| 1 ✅ | Supabase Postgres: 8 tables, 2 views, RLS + explicit grants. Seeds generated from the CSVs by script — **no number is hand-typed into SQL** |
| 2 ✅ | 75 hand-written service descriptions, in five languages |
| 3 ✅ | Embeddings: 75 service + 613 query vectors, local model, **no API key anywhere** |
| 4 ✅ | The abstention threshold, calibrated against Part A's labelled pairs |
| 5–10 ⬜ | Search RPC, behaviour screens, staff panel, demand loop, acquisition brief, deploy |

### What the build found — things the analysis could not produce on its own

| # | Finding | Why it matters |
|---|---|---|
| **B1** | **The system *can* tell "we stock nothing for this" from "we stock something."** AUC **0.805** across all 751 labelled pairs, **0.934** on the 147 the analysis is confident about (90.1% of search volume) | A5 says Part A could never verify which deals came back. This is the first evidence the failure is **detectable**, not just diagnosable. It is what makes A2's `nowhere` bucket actionable |
| **B2** | **Shipped threshold LOW = 0.40** → **6.8% false-confident / 23.2% false-abstain by search volume.** Two rates, never blended | False-confident *is* F1, the failure the prototype exists to fix. A single accuracy number would hide which mistake is being made |
| **B3** | **HIGH is not calibrated and never can be from this data.** `coverage` labels *stocked vs absent*, which is what LOW separates. Nothing labels *confident vs adjacent* | Reported as a judgement. Calling it calibrated would be the fitting the sweep exists to avoid |
| **B4** | **The prototype found a weakness in the analysis that produced it.** 99% of the expensive error sits on typo rows: the embedding correctly matched `sallee de sport` → *Abonnement Salle de Sport*, and was scored **wrong** because the hand-built concept map could not map the typo | The semantic layer repairs a Part A defect. Those rows are 9.9% of search volume, so **no published figure moves** |
| **B5** | **A3's fix is narrower than "language stops mattering."** The multilingual model bridges *phrasing* (`thai massage` ↔ `massage thai` = 0.990) but not *vocabulary divergence* (`sports massage` ↔ `masaje descontracturante` = 0.119). By English-side dead ends: **68.2% bridge well, 18.5% partial, 13.3% do not** | **52% is an upper bound** on what this fix delivers, not an estimate of it |
| **B6** | **Two security defects, both found by attacking the database rather than reading the migration.** (1) Supabase grants `anon` TRUNCATE by default and RLS does not cover TRUNCATE — `anon` wiped three tables. (2) Local and remote carry **opposite** default ACLs, so verifying security locally **proved nothing about production** | Not graded, but it is the clearest example of "claims survive checking" applied to our own work |

### What it does when it has no good answer — the brief's explicit hard requirement

Specified in `006-one-page/SPEC.md` §3.1 as screens **S1–S7**. The rule that binds them:

> **The abstention comes first, and the alternative is labelled as an alternative.**

A system that silently substitutes *is the defect* — observed live as `kitesurf` → *Barista **Kit***.
A system that names what it could not match, then offers something clearly marked as something else,
is the fix. Concretely: `fallschirmspringen` (DE) → honest empty state + demand capture, because no
skydiving exists anywhere in that market and no amount of search work creates it.

### Proposals evaluated and cut, with the evidence

Recorded because the brief grades judgement, and a cut with a number is worth more than a feature.

| Proposal | Verdict |
|---|---|
| *"Answer is in another city — show the route, offer a taxi"* | **Cut.** The whole another-city population is 145 dead ends (3.1%), composed of hair 62 · karting 21 · gym 18 · nails 10. Nobody travels between cities for a haircut |
| *"…but gate it on price — over \$100 it's worth the trip"* | **Sound rule, wrong catalogue.** 2.88% generous / 0.38% strict. The ceiling is \$179.46 and the concepts worth travelling for — skydiving, helicopter, ballooning — have **zero deals**. Ships in Part C as a production recommendation |
| *"No helicopter? Offer a balloon ride"* | **Cut as stated.** Balloon is equally absent — 0 deals match balloon/helicopter/skydive/parachute/paraglide/bungee. That swap ships the F1 bug as a feature |
| *"Log who searched"* | **Cut.** No user IDs, sessions or purchase history exist. Building it means fabricating evidence |

---

## Part C — the writeup

> *Two pages max: what was found with numbers; what was built and why **rather than the other
> options**; next steps with engineering and what the platform teams who own search globally must
> supply; how success is measured and what would signal it was not working. Plus a log: hours, which
> AI tools did what, and what they got wrong that had to be caught.*

**Status: not started. It is now the larger of the two remaining risks.**

Every input exists. Mapping their four bullets to what is ready:

| Their bullet | Ready |
|---|---|
| What you found, with numbers | A1–A7 above; `FINDINGS.md` is the source |
| What you built and **why rather than the alternatives** | `001-part-b/SPEC.md` §11 (D1–D6), `006-one-page` G1–G6, `007-embeddings` E1–E8 — every decision with its rejected alternative |
| Next steps + what the platform teams must supply | Ranked in `INDEX.md` 5.3, and **A7 makes the ask concrete**: expose match provenance — a relevance score, a matched-term field, a spell-correction field. None exist in the production API today |
| How success is measured, and what would signal failure | Dead-end rate (52.5%) replaces zero-result rate (29.3%). The failure signal is the one to write carefully |

### The tools-and-corrections log — six entries ready, each with what caught it

| # | Claim made | How it was caught | What replaced it |
|---|---|---|---|
| 1 | Live London "stocks adrenaline **abundantly**" | Those were multi-word counts, inflated by the very fragment-matching defect the same section described. Probing Berlin and Paris with single tokens exposed it **the same day** | Thin in production too: skydiving 2/3/3 across London/Berlin/Paris |
| 2 | F5 = "ranking cutoff", 40% recoverable | An inference from an *absence* with a competing explanation the CSVs cannot rule out | Withdrawn to zero. Moved the headline ~18% → **~12%** |
| 3 | "Polish diacritics cost 4× recall" | Read off coarse UI buckets with an unpinned location | Exact counts: −41% on multi-word, −8.8% single-token |
| 4 | Security verified — on the local database | Pushing to production revealed **opposite default ACLs**; local verification proved nothing | Privileges stated absolutely: revoke all, then grant back |
| 5 | Cross-lingual check passing | It hardcoded three query strings **not in the log**, so every case silently skipped and the criterion passed on nothing | Reads pairs from the analysis's own matched set |
| 6 | Drop the category tokens from the embedded document | Six hand-picked cases said obviously yes; **all 751 pairs said no** (AUC 0.805 vs 0.793) | Format unchanged |

**Entries 4, 5 and 6 are mistakes in this build, not in the analysis.** They are here on purpose.

---

## Against their stated grading criteria

| They assess | Where the package answers it |
|---|---|
| **Finding what is actually going on**, not the first thing that looks like a finding | A1 (29.3% is the wrong number) and A2 (re-spun from *why* to *where*, which assigns an owner). A4 says search is a *minority* of the opportunity — the opposite of the flattering answer |
| **Whether the prototype reflects the analysis** rather than being a search UI bolted on beside it | The class comes from `query_classes.csv` — a table in the database — **not** from a threshold (D1). Screens are specified per Part A failure class. The threshold is calibrated against Part A's own labels, and the disagreement rate is published |
| **Whether claims survive checking** | Every number regenerates from a committed script. Six withdrawn claims are listed above with what caught them. D2 is enforced by a test that fails the build, not by discipline |
| **Honesty about the limits of what was built** | A5 is stated rather than engineered around — no query→deal table exists in the schema, and the `COMMENT ON SCHEMA` says why. B3 admits HIGH is uncalibrated. B5 narrows our own recoverability claim |
| **Output per hour** | Hours are the owner's to log. The build is deliberately small: pgvector inside Postgres rather than a second system, 75 documents rather than 568, no index at this size |
| *Not assessed: code quality, tests, visual design* | Taken at face value. No test suite. Visual design was reversed to match `docs/design` by owner decision, recorded as a reversal |

---

## What is missing, plainly

1. **Part C is not written.** Largest remaining risk.
2. **No UI.** The backend is real; nothing is clickable yet. The brief says *prototype, not a deck* — until step 5 lands, this package does not meet its central requirement.
3. **The remote deployment lags local** by one migration and the current seed.
4. **The 75 descriptions have not been reviewed line by line.** The guard proves nothing *harmful* is in them; only a human confirms nothing is *wrong*.
5. **`HIGH` is a judgement**, and no amount of further work on this dataset changes that.
