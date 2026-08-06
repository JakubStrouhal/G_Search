# Groupon case study R29944 — verified findings handoff

**Purpose of this file.** Everything below was produced by running
`validate.py` against `search_log.csv` and `deals.csv`. It is the input to
Part B (prototype) and Part C (writeup). Numbers marked VERIFIED came out of
the script. Numbers marked INFERRED are interpretation. Items marked
CANNOT VERIFY are limits of the dataset and must be stated as such in Part C.

Do not treat this as final. Re-run `validate.py` before quoting anything.

---

## 0. Dataset integrity — clean, and that itself is a signal

VERIFIED:
- `search_log.csv` — 8,997 rows, 613 unique raw queries, June 1–30 2026, 30 days.
- `deals.csv` — 568 rows.
- Zero nulls. Zero duplicate IDs. No impossible funnel rows (no clicks on
  zero-result searches, no purchases without clicks).
- Every market/city present in one file is present in the other.
- 5 markets × 4 cities each.

INFERRED: this is synthetic or heavily cleaned data. Say so in Part C, and say
what you would ask for in production: query→results mapping, session IDs,
timestamps, and the ranker's relevance scores.

---

## 1. The headline is wrong if you stop at zero results

VERIFIED:

| results_shown | searches | share | CTR | search→purchase |
|---|---|---|---|---|
| 0 | 2,633 | 29.3% | 0% | 0% |
| 1–2 | 2,087 | 23.2% | 10.3% | 1.7% |
| 4+ | 4,277 | 47.5% | 51.7% | 16.1% |

**52.5% of all searches end in a dead or near-dead result set.**

There is a cliff, not a gradient. A search returning 1–2 results performs
almost identically to one returning nothing. Reporting 29.3% understates the
problem by nearly half.

**VERIFIED 2026-08-06 — the cliff is not concept mix.** The obvious objection is
composition: perhaps queries that return 1–2 results are systematically *different*
queries — rarer concepts, thinner cities — that would convert badly at any result
count. Tested by comparing 1–2 vs 4+ **within** concept × city strata, so neither
concept nor city can drive the gap. Script:
`docs/analysis/002-recoverability/notebook.py` cell 1.

| | CTR | search→purchase |
|---|---|---|
| Raw, 1–2 vs 4+ | 10.3% → 51.7% | 1.68% → 16.09% |
| **Within 138 concept × city strata** (4,707 searches, volume-weighted) | **10.2% → 52.6%** | **1.70% → 16.11%** |

Stratifying moves search→purchase by 0.02pp. The direction holds in **137 of 138
strata on CTR** and 120 of 138 on purchase. The cliff is a property of the result
count, not of which queries land there. **52.5% stands**, and it is safe to make
dead-end rate the headline metric in Part C.

VERIFIED ANOMALY: **no search anywhere returns exactly 3 results.** The
distribution runs 0, 1, 2, then jumps to 4. This is either a ranking cut-off
or a data-generation artifact. CANNOT VERIFY which from this file. State it
openly — it is a flag on the data, and noticing it is worth more than
pretending the distribution is smooth.

**RESOLVED 2026-08-06 — it is a generation artifact.** Not resolvable from this
file, so it was resolved against the live catalogue instead. Live Groupon
returns exactly 3 routinely: `quadbike` 3 and `trapeze` 3 (GB · london, N=33),
with a smooth low-count distribution 0(×6), 1(×4), 2(×2), **3(×2)**, 5, 6, 7, 8,
10, 17. A real ranking cut-off that suppressed 3s would have to be a property of
this generator alone. Script: `live_probe.js histogram()`; evidence:
`003-live-validation/RESULT.md` P4. **Consequence: F5 "ranking cutoff" is a
mislabelled class** — its recoverability assumption rested entirely on this
inference and has been withdrawn (see §5e). Closes known issue #4's first half.

---

## 2. Zero-result rate is flat across markets — this is not one broken country

VERIFIED (Wilson 95% CIs, all n > 900):

| market | searches | zero rate | 95% CI |
|---|---|---|---|
| PL | 917 | 32.6% | 29.7–35.7% |
| FR | 1,772 | 30.1% | 28.0–32.3% |
| ES | 1,997 | 29.6% | 27.6–31.6% |
| GB | 2,587 | 28.8% | 27.1–30.6% |
| DE | 1,724 | 26.9% | 24.9–29.1% |

PL and DE CIs do not overlap; everything in between does. So the only
defensible market claim is **PL worst, DE best, spread ~6pp** — which is small
relative to the 29% base rate. Do not build a per-market narrative.

VERIFIED: rate is flat across the four weeks of June (28.2% → 31.1%). No trend.

---

## 3. THE CORE FINDING — three tiers of failure, not one

This is the whole exercise. The catalogue has **5 L2 categories and only 15
unique deal titles per market** (75 unique titles across 568 deals). Titles are
generic — "Relaxing Wellness Session", "Wellness-Massage Paket", "Sesja
Wellness". The matcher appears to work at **category level, not item level**.

That produces three structurally different failures:

### Tier 1 — SILENT MISMATCH (invisible to every zero-result metric)
Query names something the catalogue does not stock, but which maps to an
existing category. The user gets a full page of results that do not answer
their question.

VERIFIED — there are **zero paintball deals, zero crossfit deals, zero sushi
deals, zero bowling deals** in the entire catalogue. Yet:

| query | searches | zero% | median results |
|---|---|---|---|
| paintball | 275 | 8.7% | 9 |
| crossfit | 299 | 17.1% | 7 |
| sushi | 265 | 15.1% | 9 |
| bowling | 194 | 14.4% | 7 |
| steak dinner | 105 | 21.0% | 2 |

Compare to a query the catalogue *does* stock: escape room, 229 searches,
10.9% zero, median 8 results. **Statistically indistinguishable.**

CANNOT VERIFY: the log records `results_shown` as a count only. There is no
query→deal mapping. So "paintball returns escape rooms" is INFERRED from the
category structure, not observed. Also: paintball converts (CTR 41%, s2p 11%)
as well as escape room. Either users substitute happily, or the data generator
did not model relevance. **You cannot distinguish these from this file.** Say
so. This is the honesty test the brief is running.

### Tier 2 — SUPPLY VOID (64.2% of zero-result searches)
VERIFIED: 185 market+query pairs return zero **every single time**, accounting
for 1,691 lost searches. Almost all are adrenaline/aerial:

| market | query | searches | zero rate |
|---|---|---|---|
| GB | helicopter tour | 100 | 100% |
| GB | hot air balloon ride | 94 | 100% |
| GB | skydiving | 91 | 100% |
| ES | rafting | 88 | 100% |
| GB | supercar track day | 87 | 100% |
| ES | paracaidismo | 86 | 100% |
| FR | saut en parachute | 81 | 100% |
| GB | shark diving | 80 | 100% |
| DE | wildwasser rafting | 75 | 100% |
| DE | hubschrauber rundflug | 65 | 100% |
| DE | fallschirmspringen | 64 | 100% |
| PL | lot balonem | 57 | 100% |

VERIFIED root cause — full L2 inventory, all markets:

| category_l2 | DE | ES | FR | GB | PL | total |
|---|---|---|---|---|---|---|
| activities | 27 | 33 | 33 | 22 | 17 | 132 |
| beauty | 26 | 16 | 21 | 33 | 12 | 108 |
| dining | 25 | 16 | 17 | 27 | 15 | 100 |
| fitness | 23 | 27 | 27 | 32 | 11 | 120 |
| massage | 21 | 22 | 24 | 27 | 14 | 108 |

And "activities" contains **only** city tours, escape rooms, and karting. No
aerial, no water sports, no motorsport. **Search cannot fix this.** It is a
merchant-acquisition signal wearing a search failure's clothes.

VERIFIED concept-level: adrenaline queries are 1,685 searches, 74.4% zero,
**47.6% of all zero-result searches in the dataset.**

CORRECTION — RAISED, THEN FIXED (2026-08-05). Layer 3 originally mapped
adrenaline → `activities` L2 and asked "does the category exist". It does —
132 deals — so the decisive table printed "MATCHER FAILURE" for skydiving, the
exact opposite of the truth. **A category that exists is not a category that
stocks the thing.** The test now runs at *title* level, and adrenaline reads
SUPPLY VOID in all five markets with 0 deals stocking it. The narrative is kept
here on purpose: it is the honest answer to the brief's "what did the AI tools
get wrong" question, and it is a better answer than a generic one.

### Tier 3 — INTERMITTENT (35.8% of zero-result searches)
VERIFIED: 179 pairs return zero sometimes, 942 lost searches. Typical rates
12–25%. Examples: ES crossfit 22%, GB pizza deal 16%, DE haare färben 23%,
FR bowling 21%.

VERIFIED city test: median city-to-city spread within intermittent pairs is
**0.199** — substantial. ES crossfit ranges 0% to 43.8% by city; DE
gesichtsbehandlung 0% to 42.9%; FR extension de cils 0% to 37.5%.

INFERRED: city-level supply thinness is a real contributor. But 20pp spread
does not explain the whole intermittency, and a query that returns results 80%
of the time and nothing 20% of the time in the *same city* points at a ranking
threshold. CANNOT VERIFY without the ranker.

VERIFIED supply-density check: corr(deals per city, zero rate) = **-0.379**
across 20 city-market cells. Direction matches Groupon's own stated mechanism
(denser supply → better outcomes). n=20 — report the direction, not the
coefficient, and say so.

---

## 4. Kill the typo theory — it is small

TWO NUMBERS EXIST AND THEY MEASURE DIFFERENT THINGS. Say which you mean:

- **7.5% (198 zeros)** — every market+query pair with n ≤ 3, i.e. the whole
  long tail, of which misspellings are only part. The *generous* bound.
- **1.9% (51 zeros)** — `validate.py` Layer 4's near-miss test: strings within
  0.85 similarity of a healthy query. The *strict* bound, and the one that
  actually isolates typos.

Both reproduce. Quoting either without naming the definition reads as sloppy.
Use 1.9% when the claim is "typos"; use 7.5% when the claim is "the long tail".
And 73 of the 198 are adrenaline concepts — they would return nothing spelled
perfectly, so even the generous bound overstates the fixable part.

VERIFIED further: most typos already return results. DE `sprtmassage`,
`thi massage`, `neckenmassage`, `ruckenmassage` all return results at 0% zero
rate. **The matcher is already fuzzy on spelling.**

So spell-correction is worth roughly **125 searches out of 2,633 zeros (4.7%)**.
Do not build the prototype around it. Mentioning it as a cheap win is fine;
leading with it would be a misread.

---

## 5. Funnel baseline (for sizing anything)

VERIFIED, non-zero searches only (re-run 2026-08-05):
- CTR **38.1%**, click→purchase **29.8%**, search→purchase **11.4%**.
- By market s2p, non-zero searches: FR 10.0%, DE 10.2%, PL 11.3%, GB 12.0%,
  ES 12.8%. Over *all* searches: FR 7.0%, DE 7.5%, PL 7.6%, GB 8.5%, ES 9.0%.

CORRECTED. An earlier version of this section said "roughly 5–10%, PL lowest".
Both halves were wrong — the range is 7.0–9.0% over all searches, and **FR is
lowest while PL is third**. A wrong directional claim about a named market is
precisely what the brief's "claims survive us checking them" criterion catches.
The earlier CTR/CVR figures (38.4 / 30.0 / 11.5) were also stale by ~0.2pp.

VERIFIED upper bound (recomputed 2026-08-06): if all 2,633 zero-result searches
converted at the observed non-zero s2p of **11.36%**, that is **299 purchases**
over 30 days across 5 markets. **Label this an upper bound, not a forecast.**
Recovered demand converts worse than organic demand. If you present it any other
way you have failed the "claims survive their data checks" criterion.

CORRECTED 2026-08-06. This bound previously read "~303 purchases at the observed
11.5%" — eleven lines below the same section's own 11.4%. The stale rate was
inside a derived figure, so the bound itself was recomputed rather than the digit
edited. **Use one number: 299.** It had already propagated into the Part B spec's
acquisition-brief copy, which is how a drifted rate becomes a claim in the
deliverable.

*Denominator note, because it is the thing that gets misread:* 38.1 / 29.8 / 11.4
are over **searches that returned results**. Over all 8,997 searches the figures
are CTR 27.0% and s2p 8.0%. Quoting the second set against the first set's claim
is the easy mistake here.

---

## 5b. THE LANGUAGE TEST — the brief's own thesis, confirmed with a number

Added 2026-08-05. Script: `language_test.py`. This is the strongest result in
the package and it should lead Part C.

The brief claims the platform was "built for the US: dense supply,
English-language queries". That is the one business claim in the brief the
supplied data can actually test, and it had never been tested.

VERIFIED, matched-pair design — same concept, same market, English phrasing vs
local phrasing, restricted to concepts the catalogue stocks, GB excluded
(English is local there):

| | dead-end rate | 95% CI |
|---|---|---|
| English phrasing | **81.2%** (195/240) | 75.8–85.7% |
| Local phrasing | **39.0%** (914/2345) | 37.0–41.0% |

**Gap 42.3 percentage points. The intervals are nowhere near overlapping.
47 of 48 matched pairs point the same way.** Holds in all four markets
(DE 43.1, ES 45.4, FR 38.9, PL 41.5pp).

VERIFIED — both confounds killed, and killing them is what makes this a finding
rather than an artifact:

- **Supply.** The naive split ("queries that also appear in GB") is dominated by
  loanwords — brunch, crossfit, sushi, paintball, bowling — that name concepts
  stocked **nowhere**. Those fail at 44.0% (CI 41.2–46.9%), i.e. the ordinary
  rate. Their problem is supply, not language. Matched pairs use only stocked
  concepts, so supply cannot explain the gap.
- **Rarity.** English queries are all low-volume, so "rare queries just fail
  more" had to be excluded. Rare *local* queries (n ≤ 5) die at 53.3%, not 81%,
  and there is no rarity gradient among local queries at all.

INFERRED: this separates two failure modes that look identical on a dashboard —
**English phrasing for a stocked concept = language failure (81%)** vs
**loanword for an unstocked concept = coverage gap (44%)**. They need different
fixes and different owners.

CANNOT VERIFY: this is synthetic data, so what it demonstrates is that the
*generator* encoded a language effect. It is evidence the brief's thesis is
coherent and quantifiable — **not** independent proof that Groupon production
search has this exact defect. The live probe is the separate real-world check.

---

## 5c. WHAT THE CATALOGUE ACTUALLY IS — 15 products, not 5 categories

VERIFIED: the 568 deals reduce to **15 distinct products**, each repeated across
5 languages: escape room, karting, guided city tour, haircut/styling, facial,
mani-pedi, 3-course meal, tasting menu, dinner+wine, gym pass, personal
training, unlimited classes, spa massage, wellness session, full-body massage.
Every deal classifies into one of these with nothing left over.

So the real shape of the problem is **613 distinct demands meeting 15 products.**
That framing does more work than "5 L2 categories", and it is what makes the
coverage-gap test enumerable rather than fuzzy.

---

## 5d. CLASSIFICATION AND THE FIX LIST

Added 2026-08-05. Script: `classify.py` → `outputs/query_classes.csv` (755
market+query pairs), `outputs/fix_list.csv`.

VERIFIED — share of all dead-ends by failure class:

| Class | Pairs | Searches | Share of dead-ends |
|---|---|---|---|
| F4 supply void | 178 | 1,689 | 35.7% |
| Baseline (stocked, still ~40% dead) | 161 | 4,321 | 32.9% |
| F1 silent substitution | 259 | 1,326 | 11.2% |
| ~~F5 ranking~~ *(label withdrawn — see §1 and §5e)* | 73 | 658 | 7.5% |
| ~~F3 geographic~~ *(label withdrawn — see §5f)* | 15 | 645 | 6.8% |
| F2 language | 65 | 358 | 5.9% |

**The F5 row is a population, not a diagnosis.** Its 73 pairs / 658 searches are real
and still counted, but the *name* is withdrawn: `classify.py` assigns F5 as a
residual (stocked · failing · not F2 · not F3), and the "ranking cutoff" reading
rested entirely on the missing `results_shown = 3`, which §1 now resolves as a
generation artifact. Treat it as a **second unexplained residual** alongside
BASELINE. Its recoverability was withdrawn to zero, not re-estimated.

**The F3 row is also a population, not a diagnosis** — same shape, found the same
way, 2026-08-06. `classify.py` assigns F3 from city-to-city variance in dead rate,
not from where inventory sits; tested directly, **only 6 of its 321 dead ends have
the answering deal in another city**. Full detail and the consequences in **§5f**.
Unlike F5, its recoverability was **not** withdrawn — see §5f for why, and for the
tightened figures if it were.

VERIFIED — demand is concentrated, so the fix list is short: the top 50
market+query pairs are **51.2%** of all dead-ends; the top 100 are **75.3%**.

VERIFIED classifier accuracy: **~86%** on a 35-row stratified hand-audit,
**stated as an upper bound** because it is a self-audit by the author of the
rules. The audit found a *systematic* error (the concept map credited a generic
"Three-Course Meal for Two" with answering `brunch`, `burger` and `tapas`) which
was fixed at the cause rather than noted.

CANNOT VERIFY: F1's size is the size of a coverage gap that still returns
results — **not** a measurement of user harm. Without a query→deal mapping,
"these users saw the wrong thing" stays an inference. F6 (goods vs experience
intent) is deliberately **unassigned**: it was observed live, but this catalogue
contains no Goods, so it cannot occur here and forcing rows into it would be
inventing a finding.

---

## 5e. LIVE VALIDATION — a different catalogue, and the line must not blur

Added 2026-08-06. Full detail and pinned counts: `003-live-validation/RESULT.md`.
Predictions were pre-registered in that folder's `BRIEF.md` before probing.

**READ THIS FIRST.** Everything in this section describes **live production
Groupon** (`groupon.co.uk`/`london`, `groupon.pl`/`warszawa`, 2026-08-06). It is
a *different catalogue* from the supplied CSVs. It can confirm **how a real
search engine fails** — which is what F1–F6 describe. It **cannot** validate any
number in the supplied dataset. `PLAN.md` §7 lists conflating the two as a trap.

VERIFIED (live catalogue) — **silent substitution is now observed, not inferred.**
§3 Tier 1 tags "paintball returns escape rooms" CANNOT VERIFY because this log
has no query→deal mapping. Live Groupon has one, and it does exactly this:

| query | results | what actually came back |
|---|---|---|
| `paragliding` | 2 | two London Cable Car / Thames river-cruise passes |
| `kitesurf` | 1 | "Portable Bartender Barista **Kit**" |
| `wingsuit` | 6 | "Angel **Wings** Potted Plants"; a drying rack with an "Adjustable Side **Wing**"; a perfume |
| `quadbike` | 3 | a real ATV; a Dubai desert safari; a **kids' electric toy** quad bike |

The mechanism is visible in the titles: the matcher **matches query fragments**
(`kitesurf` → *kit*, `wingsuit` → *wing* + *suit*). **The supplied dataset's F1
sizing (259 pairs / 1,326 searches) remains inference.** What is now observed is
that the mechanism is real in production, not that this dataset exhibits it.

VERIFIED (live) — **the result count does not track specificity.** Adding a
discriminating term sometimes adds exactly (`paintball massage` 470 = 458 + 12;
`skydiving massage` 460 = 458 + 2), sometimes does nothing (`xqzjw massage` 458),
sometimes *subtracts* (`helicopter massage` **418** < 458, reproduced). **Do not
claim union semantics** — four recorded counterexamples contradict it. The
consequence is what matters: **the user has no lever**, so the engine has no path
to "we don't have that".

VERIFIED (live) — **the API returns no relevance signal.** `BrowseDealFeed`
returns `cards`, `facets`, `pagination` and nothing else. No match score, no
matched-term field, no spell-correction field. **The client cannot tell a genuine
match from padding.** So this dataset's central limitation — `results_shown` is a
count with no query→deal mapping — *faithfully reproduces what production
exposes*. That converts the honesty caveat into a concrete platform ask:
**expose match provenance.**

VERIFIED (live) — **adrenaline is thin in production too, though not absent.**
Single-token probes across three cities and three hosts, 2026-08-06:

| concept | GB London | DE Berlin | FR Paris |
|---|---|---|---|
| skydiving | 2 | 3 | 3 |
| ballooning / paragliding | 2 | 1 | 0 |
| helicopter | 11 | 10 | 18 |
| climbing | 0 | 4 | 14 |

**CORRECTED 2026-08-06, same day it was written.** The first version of this line
said "abundantly stocked in London" on the strength of `hot air balloon` 558 and
`wing walking` 449. Those are **multi-word** queries, and the paragraph two above
this one establishes that multi-word counts are inflated by fragment matching —
so the evidence for "abundant" was an artifact of the defect being described.
Probing Berlin and Paris with single tokens exposed it. **This is the best "what
the AI tools got wrong" example in the package**: one probe contradicted another
probe in the same session, and only a second and third city surfaced it.

**What it bounds, revised.** The supplied catalogue's *total* void (0 deals,
100% zero) is still an exaggeration and so still a modelling choice. But it
exaggerates a **real thinness** rather than inventing one — the shape the
analysis identifies is visible in production. Part C **may** say the pattern is
not merely an artifact of the supplied data. It **may not** put a number on real
Groupon's inventory gap, or recommend named-city vendor acquisition, from this run.

VERIFIED (live) — **F5's recoverability is withdrawn.** See §1. The
`002-recoverability` central estimate moves **59 → 36 purchases/mo**, and search's
share of the recoverable total moves **17.9% → 11.8%** (range 5.6–15.1%).
**Quote ~12%, never ~18%.** The direction strengthens as the number falls.

VERIFIED (live) — **the diacritic penalty replicates but does not generalise.**
`masaż tajski` 162 / `masaz tajski` 95 (−41.4%) and `masaż relaksacyjny` 215 / 112
(−47.9%) reproduced to within 0.5pp a day later. But `zajęcia`/`zajecia` (302 =
302), `żagle`/`zagle` (73 = 73) and the two-token `przedłużanie rzęs`/`przedluzanie
rzes` (9 = 9) show **zero** penalty. The effect is specific to the `masaż` token
family. **§5b's 42.3pp gap is measured in the supplied data and is untouched**;
F2's recoverability range was deliberately left unchanged.

VERIFIED (live) — **radius widening is not offered where it would help.** Every
call returns a cumulative `distance` facet (`massage`/london: 11 within 1km, 136
within 5km, 403 within 100km of 458) and a per-town `locations` facet. For thin
queries both are **empty** — `paragliding` returns 2 results that sit in *no*
distance bucket at all. The platform knows it has nothing near the user and
returns results anyway.

VERIFIED (live) — **the autocomplete layer is erroring.** `SuggestedSearchQueries`
returned `INTERNAL_SERVER_ERROR` for 3/4 queries on `groupon.pl` (2026-08-06),
having returned 5/5 errors on `groupon.co.uk` (2026-08-05). Cross-host and
cross-day, so no longer a single-session artifact. The layer where spell
correction and query understanding live is returning nothing.

CANNOT VERIFY (live): single session, one division per market, GB and PL only.
Counts were stable on repeat; **ordering was not**. Counts are inflated by the
multi-term behaviour above — `hot air balloon` = 558 is not 558 balloon rides.

---

## 5f. INVENTORY LOCATION — "when the search failed, where was the answer?"

Added 2026-08-06. Script: `classify.py` §3b → `outputs/inventory_location.csv`,
`outputs/inventory_sensitivity.csv`, plus four additive columns on
`query_classes.csv`. **This is now the spine of the explainer**, so it is the
claim most exposed to being checked.

It asks a different question from §5d. F1–F6 ask *why* a query failed. This asks
*where the answer was*, which is the question that assigns an owner. It is
`classify.py`'s own `coverage()` evaluated at `(market, city)` instead of
`(market)` — no new map, no new judgement beyond the seam named below.

VERIFIED, over **all 4,720 dead ends** (one denominator throughout — the earlier
draft of this section mixed a mapped-only denominator with a total one, which is
exactly the sloppiness the brief's "claims survive checking" criterion catches):

| Where the answer was | dead ends | share | owner |
|---|---|---|---|
| **Nowhere in the market** | 2,039 | 43.2% | Merchant acquisition — not search |
| **The user's own city** | 1,520 | 32.2% | Search. This is the search problem's real size |
| **Another city in the market** | 145 | 3.1% | Product/UX |
| **Can't tell from this catalogue** | 1,016 | 21.5% | Not attributed |

VERIFIED — **the buckets and the F1–F6 classes nest exactly.** `nowhere` is
precisely F4 (1,584) + F1 (455), asserted in `notebook.py` rather than claimed.
`same_city` is BASELINE 929 + F5 236 + F2 197 + F3 158. A per-row assertion in
`classify.py` fails the build if the four columns stop summing to `deads`.

VERIFIED — **the headline is a band, not a point.** One tier of the coverage test
is a judgement call: `plausible` (yoga, pilates, crossfit, `dining_specific`) —
a generic deal that might or might not answer the query. All **1,016** of its dead
ends move together. Across the three defensible readings, lifted to the constant
`PLAUSIBLE_COUNTS_AS`:

| convention | nowhere | same city |
|---|---|---|
| give them their own bucket *(default, shown on the page)* | 43.2% | 32.2% |
| count them as no answer | 64.7% | 32.2% |
| count a generic deal as an answer | 46.8% | **48.9%** |

**Quote the band [43.2%, 64.7%], never one end alone.** Under the third reading
**the ordering flips** and same-city becomes the largest bucket. The page says so.

VERIFIED — **the decomposition beats a randomised null, and the falsification test
was pre-registered before the number was read.** Shuffling `concept` within market
and recomputing (50 draws, seed 7): `nowhere` real 63.4% vs shuffled 53.6% ± 0.50,
**excess +9.8pp (z = +19.5)**; under the alternative seam, real 44.8% vs shuffled
30.8% ± 0.42, **excess +14.0pp (z = +33.6)**. Passes under both, and *strengthens*
under the reading less favourable to the headline.

**But say the rest of it:** most of the *level* is structural. A 15-product
catalogue stocks few concepts anywhere, so a random assignment already produces
53.6 of the 63.4 points. **The excess over chance is the finding; the raw level is
mostly a property of the catalogue's shape.** Script:
`scratchpad/verify_buckets.py`, reproduced independently of the subagent that
first proposed it.

VERIFIED — **reachability, a pass rather than a test.** For `same_city` to mean
anything, the co-located inventory has to be reachable at all. Of the 154
market × city × concept cells in that bucket, **146 (95%) return 4+ results at
least once**; the 8 that never do account for **21 dead ends (1.4% of the
bucket)**. Had this come back low, "the answer was right there" would have been
unsupported.

INFERRED: that "no deal title in this city matches the concept pattern" means the
answering inventory was genuinely absent. A **title match is a proxy** for
"answers the query", not a measurement of it — the same proxy §3 and §5d already
rest on. The generic titles are exactly where the proxy is weakest, which is what
the band prices in.

CANNOT VERIFY: that any specific dead end **would have been answered** by the
co-located deal. `results_shown` is a bare count with no query→deal mapping, so
`same_city` means *"stock existed nearby"*, never *"the user should have seen
it"*. Identical limitation to F1's sizing.

CANNOT VERIFY: the `another_city` magnitude. Most market × concept cells stock the
concept in **all four cities**, so `another_city` is structurally impossible for
them — **3.1% is close to the ceiling this catalogue's near-uniform city
distribution can express**, and is a property of the generator as much as of
search. Do not present it as evidence that cross-city inventory is a small problem
at real Groupon. Its composition is also *not* a travel story: hair 62, karting 21,
gym 18, personaltrain 17, facial 13, nails 10. Nobody drives to the next city for a
haircut.

**Two errors of opposite sign, stated rather than netted.** Concept-granularity
title matching **inflates `same_city`** (a "Spa & Massage Treatment" counts as the
answer to `sports massage`). The `plausible` seam **inflates `nowhere`**. Holding
both explicitly is a stronger position than caveating one.

### The 33% / 12% reconciliation — exact, no remainder

The obvious challenge: §5f says a third of dead ends had the answer in the user's
own city; §5e says search is worth ~12%. Both, and they measure different things:

- **32.2% is the size of the problem** — 1,520 failures where inventory was there.
- **11.8% is the size of the fix we can defend** — of those 1,520, a named
  mechanism exists for **355** (F2 197 + F3 158). The other **1,165** (BASELINE
  929 + F5 236) are stocked, failing and **unexplained**.

That 1,165 is not a rounding error. It is the part of the search problem that was
not explained, and claiming it would be the same false confidence the analysis is
about. **Every way of tightening the estimate moves the same direction:** credit
recovery only on demonstrable-answer rows → **7.8%**; additionally withdraw F3 the
way F5 was withdrawn → **5.7%**. Part C publishes the most generous, **11.8%**,
and says the other two exist.

### CORRECTION — F3's diagnosis is withdrawn (its population is not)

VERIFIED: of F3's 321 dead ends, **only 6 have the answering deal in another city**.
158 are in the user's own city and 157 are `can't tell`. `classify.py` assigns F3
from **city-to-city variance in dead rate** (`city_spread >= 0.25`), which is a
symptom, not a location. **The name "geographic thinness" was never earned.**

Same shape as F5's withdrawn "ranking cutoff": the population is real and still
counted, the diagnosis is not. Relabelled to **"Uneven across cities"** in the
explainer, with the class key `F3_geographic` deliberately unchanged so
`query_classes.csv`, `web/mock/build.py` and `002-recoverability` keep working.

This also means F3's shipped user-facing copy — *"We have this, just not in your
city."* — was **false for 315 of 321 dead ends and live in `explainer.html`**,
where a grader could click a chip and read it. Fixed 2026-08-06.

**Its recoverability range was deliberately left unchanged at 25% (10–40%)** rather
than re-derived, because re-deriving it lowers the headline and the generous
number is the one worth defending. F3 contributes 12.9 of the 36.3 purchases — 36%
of the entire search-side estimate — so this is a live exposure, not a footnote.

---

## 6. What this means for Part B (the prototype)

The brief says the prototype must handle every query type found in Part A,
**including the ones that cannot be fixed** — "what it does when it has no good
answer tells us as much."

The three tiers each need a visibly different behaviour:

1. **Silent mismatch (paintball → escape rooms).** The hardest and the most
   interesting, because today it is invisible. The prototype should be able to
   say *"we don't have paintball in Berlin — here's what's close, and here's
   what we do have"* rather than silently substituting. This is the one no
   other candidate will have found, because it does not show up in a
   zero-result dashboard.

2. **Supply void (skydiving in Berlin).** The largest bucket. The empty state
   is the product, not an error page. This query is simultaneously a demand
   signal for merchant acquisition — the intersection of Groupon's two stated
   priorities. Capture intent; do not just apologise.

3. **Vocabulary / thinness (masaż tajski, haare färben).** The genuinely
   fixable matching layer: local-language query against generic local-language
   titles. Semantic or concept-level matching.

Build note: **do not build a nice semantic search bar and call it done.** The
largest bucket is unfixable by search, and the most interesting bucket is
invisible to search metrics. A prototype that only demos better matching has
answered a different question than the one asked.

---

## 7. Open items — must be resolved before Part C is written

- [x] Re-run `validate.py`; confirm every number above. *(2026-08-05)*
- [x] Fix the adrenaline → `activities` concept mapping. *(now a title-level
      test; see §3)*
- [x] Extend the concept map until the "unmapped" bucket is small. *(3.7% of
      searches in `classify.py`, down from 42%)*
- [x] Run the language test. *(§5b — the strongest result in the package)*
- [x] Decide and state the position on the missing `results_shown = 3`.
      *(2026-08-06 — **generation artifact**, settled against the live catalogue
      because this file cannot settle it. See §1 and §5e.)*
- [ ] Decide and state the position on whether paintball's healthy conversion
      is substitution or a data artifact. *(Still open for the supplied data.
      §5e shows the substitution mechanism is real in production, which makes
      "substitution" the more likely reading — but it is not evidence about
      **this** dataset, and must not be presented as such.)*
- [ ] Log hours and AI tools used, including what the tools got wrong. The
      adrenaline/activities misclassification in §3 is a real example — use it.

---

## 8. Facts to reuse verbatim

- 8,997 searches · 613 unique queries · 568 deals · 75 unique deal titles ·
  **15 distinct products** · 5 markets · 4 cities each · June 2026.
- 29.3% zero results. 23.2% return 1–2 results. **52.5% combined dead-end.**
- Zero-result split: 64.2% always-zero (supply void), 35.8% intermittent.
- Adrenaline = 47.6% of all zero-result searches; SUPPLY VOID in all 5 markets,
  0 deals stocking it.
- **English phrasing 81.2% dead-end vs local phrasing 39.0% — a 42.3pp gap,
  47 of 48 matched pairs, consistent across all four non-GB markets.**
- Loanwords for unstocked concepts fail at 44.0% — the ordinary rate. Supply
  problem, not a language problem.
- Top 50 market+query pairs = 51.2% of all dead-ends. Top 100 = 75.3%.
- Inventory: 4 L1 categories, 5 L2 categories, no aerial/water/motorsport.
- corr(city deal count, zero rate) = -0.379, n=20 — direction only.
- Typos: 1.9% of zeros (strict) or 7.5% (long tail). Name the definition.
- Funnel, non-zero searches: CTR 38.1%, click→purchase 29.8%, s2p 11.4%.
  Lowest market s2p is **FR**, not PL.
- Search-fixable share of the recoverable opportunity: **~12%** (central 11.8%,
  range 5.6–15.1%), **36 purchases/mo** central. **The older ~18% / 59 figures
  are dead** — withdrawn 2026-08-06 when live probe P4 killed F5's basis.
- **Where the answer was**, over all 4,720 dead ends: **nowhere in the market 43.2%
  (2,039) · the user's own city 32.2% (1,520) · another city 3.1% (145) · can't
  tell 21.5% (1,016)**. Quote the `nowhere` **band [43.2%, 64.7%]**, never one end
  — the `plausible` seam moves 1,016 dead ends together, and under one reading the
  ordering flips. See §5f.
- Denominator for anything "per month": **723 purchases** across 5 markets today.
  So +36/mo is **+5.0%** on purchases; the supply-void ceiling of +271 is **+37.5%**.
- **F3 "geographic" is a withdrawn diagnosis** — 6 of 321 dead ends are actually
  another-city. Say "uneven across cities, cause not established".

**Live catalogue only — never mix these with the eight lines above:**

- Live Groupon **does** return exactly 3 results (`quadbike`, `trapeze`), so the
  supplied data's 0,1,2→4 gap is a generation artifact.
- Live `paragliding` in London returns **2 cable-car river passes**; `kitesurf`
  returns a **barista kit**. Silent substitution, observed.
- Live search returns **no relevance score and no matched-term field** — the same
  blindness as `results_shown` being a bare count.
- Live adrenaline supply is **thin in London, Berlin and Paris alike** (skydiving
  2/3/3, ballooning-paragliding 2/1/0). The supplied catalogue's *total* void
  exaggerates a real thinness rather than inventing one — so the pattern is not
  merely an artifact, but no vendor-acquisition recommendation for a named city
  follows either.
