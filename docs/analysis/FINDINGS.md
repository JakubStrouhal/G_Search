---
created: 2026-08-06
updated: 2026-08-06
note: Split §1's missing-3s entry so F5's withdrawal rests on this file alone and only the generator diagnosis stays live-tagged; added the §5f price-gate test (a >$100 cross-city gate reaches 2.88% generously, 0.38% strictly, because the concepts worth travelling for have zero deals). Earlier: corrected the query_classes.csv pair count (755 → 751, which the §5d class table had always summed to) and consolidated twelve scattered retraction narratives — three moved out of PLAN.md — into one dated Corrections register (§9); deleted §6 and §7 and rebuilt §8 from a table of copied numbers into a table of quoting rules, since copying is what produced the 755 drift.
---

# Groupon case study R29944 — verified findings handoff

**Purpose of this file.** Everything below was produced by running
`validate.py` against `search_log.csv` and `deals.csv`. It is the input to
Part B (prototype) and Part C (writeup). Numbers marked VERIFIED came out of
the script. Numbers marked INFERRED are interpretation. Items marked
CANNOT VERIFY are limits of the dataset and must be stated as such in Part C.

**Every claim made and then withdrawn is in §9, the Corrections register — one
dated row each, and nothing else here retells that history.**

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

VERIFIED, added 2026-08-06 — **a second generation seam, above 25 results.**
Given a search returned *anything*, whether it returns **26 or more** is
statistically flat across market (6.8–8.2%), city (4.5–10.0%), coverage
(6.5–8.1%) and language (7.3% vs 8.3%) — indistinguishable from one shared
random draw (χ² p = 0.65). Landing in **1–2** is not: it is strongly predicted by
the query (χ² p = 4×10⁻¹⁶). **Keep the claim this narrow.** It is *not* true that
`results_shown` is random; it is true that the part of it above 25 carries no
query information. Consequence in §8, working in `004-data-story/notebook.py`.

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

**Two consequences, and they rest on different evidence — do not merge them.**

1. **F5's "ranking cutoff" is withdrawn, on this file's evidence alone.** The
   diagnosis, and the 40% recoverability hanging off it, were inferred *from an
   absence* whose competing explanation this file cannot rule out. An inference
   that cannot be attributed does not license a point estimate, so it is
   withdrawn to zero rather than re-derived — **§9 row 7**; §5d has how to read
   the surviving population. **No live figure is needed for this, and none is
   used.**
2. **The cause is a generation artifact** — **live catalogue, tagged as such.**
   Not resolvable from this file, so it was resolved against production instead:
   live Groupon returns exactly 3 routinely (`quadbike` 3, `trapeze` 3;
   GB · london, N=33, smooth low-count distribution). A cut-off suppressing 3s
   would have to be a property of this generator alone. `live_probe.js
   histogram()`; `003-live-validation/RESULT.md` P4. This **corroborates** (1);
   it is not its basis.

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

## 3. Failure is structured, not uniform — the first cut

The catalogue has **5 L2 categories and only 15 unique deal titles per market**
(75 unique titles across 568 deals). Titles are generic — "Relaxing Wellness
Session", "Wellness-Massage Paket", "Sesja Wellness". The matcher appears to
work at **category level, not item level**, which produces structurally
different failures that a single zero-result number averages together.

*The "three tiers" this section originally led with were the first cut at that
structure and are **superseded** — §5d replaces them with the F1–F6 taxonomy and
§5f with the four location buckets that assign an owner. The headings survive
below only as labels over the numbers they produced, which still stand and keep
their tags. Build Part C on §5d and §5f, not on the tiers.*

### Tier 1 → F1 — SILENT MISMATCH (invisible to every zero-result metric)
The query names something the catalogue does not stock but which maps to an
existing category, so the user gets a full page of results that do not answer it.

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
did not model relevance. **You cannot distinguish these from this file.** This is
the honesty test the brief is running, and it is the one question left open:
**Part C must state the ambiguity, not resolve it.** §5e shows the substitution
*mechanism* is real in live production, which makes substitution the likelier
reading — but that is a different catalogue and is **not** evidence about this
dataset.

### Tier 2 → F4 — SUPPLY VOID (64.2% of zero-result searches)
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
**47.6% of all zero-result searches in the dataset.** This test runs at *title*
level, not `category_l2` level; running it at category level produced the
opposite answer and is **§9 row 1**.

### Tier 3 — INTERMITTENT (35.8% of zero-result searches)
VERIFIED: 179 pairs return zero sometimes, 942 lost searches. Typical rates
12–25%. Examples: ES crossfit 22%, GB pizza deal 16%, DE haare färben 23%,
FR bowling 21%.

VERIFIED city test: median city-to-city spread within intermittent pairs is
**0.199** — substantial. ES crossfit ranges 0% to 43.8% by city; DE
gesichtsbehandlung 0% to 42.9%; FR extension de cils 0% to 37.5%.

INFERRED: city-level supply thinness is a real contributor, but a 20pp spread
does not explain the whole of the intermittency. **The remainder is unexplained.**
An earlier reading attributed it to a ranking threshold; that is the same causal
claim withdrawn as F5 (**§9 row 7**) and it is not made here. CANNOT VERIFY
without the ranker.

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

**The lowest market s2p is FR, not PL** — the earlier claim of "roughly 5–10%,
PL lowest" was wrong in both halves and is **§9 row 2**.

VERIFIED upper bound (recomputed 2026-08-06): if all 2,633 zero-result searches
converted at the observed non-zero s2p of **11.36%**, that is **299 purchases**
over 30 days across 5 markets. **Label this an upper bound, not a forecast.**
Recovered demand converts worse than organic demand. If you present it any other
way you have failed the "claims survive their data checks" criterion. **Use one
number: 299** — the superseded 303 is **§9 row 6**.

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

Added 2026-08-05. Script: `classify.py` → `outputs/query_classes.csv` (**751**
market+query pairs — the class table below has always summed to 751),
`outputs/fix_list.csv`.

VERIFIED — share of all dead-ends by failure class:

| Class | Pairs | Searches | Share of dead-ends |
|---|---|---|---|
| F4 supply void | 178 | 1,689 | 35.7% |
| Baseline (stocked, still ~40% dead) | 161 | 4,321 | 32.9% |
| F1 silent substitution | 259 | 1,326 | 11.2% |
| ~~F5 ranking~~ *(label withdrawn — §9 row 7)* | 73 | 658 | 7.5% |
| ~~F3 geographic~~ *(label withdrawn — §9 row 10)* | 15 | 645 | 6.8% |
| F2 language | 65 | 358 | 5.9% |

*(178 + 161 + 259 + 73 + 15 + 65 = 751, the row count of `query_classes.csv`.)*

**How to read the two struck rows: they are populations, not diagnoses.** Both
names were withdrawn (§9 rows 7 and 10); both populations are real and still
counted at the pairs and searches above.

- **F5** is a residual by construction (`classify.py`: stocked · failing · not F2
  · not F3) — a **second unexplained residual** alongside BASELINE. Recoverability
  withdrawn to zero, not re-estimated.
- **F3** is a population with **high city-to-city variance in dead rate**
  (`city_spread >= 0.25`) — a symptom, not a location. Relabelled **"Uneven across
  cities"**. Unlike F5, its recoverability was **not** withdrawn; §5f holds why.
  *(Its 645 **searches** contain **321 dead ends** — that is the denominator §5f
  and §9 row 10 use. Not a second figure for the same thing.)*

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
number in the supplied dataset. **Conflating the two voids the package:** the
live pass evidences how the matcher fails, never what the supplied catalogue
contains. Never mix a live figure into a dataset claim or the reverse.

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

**Single tokens only, and that is load-bearing** — multi-word counts are inflated
by fragment matching (two above), so they cannot evidence abundance. Two claims
built on them were withdrawn: **§9 rows 8 and 9**.

**What it bounds.** The supplied catalogue's *total* void (0 deals, 100% zero) is
still an exaggeration and still a modelling choice — but it exaggerates a **real
thinness** rather than inventing one. Part C **may** say the pattern is not merely
an artifact of the supplied data. It **may not** put a number on real Groupon's
inventory gap, or recommend named-city vendor acquisition, from this run.

VERIFIED (live) — **F5's recoverability is withdrawn.** See §1 and §9 row 7. The
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
returned `INTERNAL_SERVER_ERROR` for 3/4 queries on `groupon.pl` (2026-08-06) and
5/5 on `groupon.co.uk` (2026-08-05) — cross-host and cross-day, so not a
single-session artifact. The layer where spell correction and query understanding
live is returning nothing.

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

VERIFIED, over **all 4,720 dead ends** — one denominator throughout, which an
earlier draft of this section got wrong (**§9 row 11**):

| Where the answer was | dead ends | share | owner |
|---|---|---|---|
| **Nowhere in the market** | 2,039 | 43.2% | Merchant acquisition — not search |
| **The user's own city** | 1,520 | 32.2% | Search. This is the search problem's real size |
| **Another city in the market** | 145 | 3.1% | Product/UX |
| **Can't tell from this catalogue** | 1,016 | 21.5% | Not attributed |

**Do not lift 43.2% out of this table on its own.** It is the *default* reading of one
judgement call (`PLAUSIBLE_COUNTS_AS`, below). The honest figure is the band
**[43.2%, 64.7%]**, and under one of the three readings same-city overtakes nowhere.

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

VERIFIED 2026-08-06 — **price-gating the cross-city offer does not rescue it.** The
proposal was to show the trip only when the answering deal is expensive enough to
justify it (>$100). Script: `006-one-page/price_gate.py`, which imports
`classify.py`'s `STOCK_TITLE` rather than restating it.

| gate | dead ends | share of all 4,720 |
|---|---|---|
| `another_city` at all | 145 | 3.07% |
| ≥1 answering deal > $100 (generous) | **136** | **2.88%** |
| median answering deal > $100 (strict) | **18** | **0.38%** |

Composition is unchanged by the gate — the generous 136 are largely $100+ hair
packages and gym memberships. **The reason the rule cannot pay off here is itself
the finding: the catalogue's price ceiling is $179.46, and the concepts whose price
would justify a trip — skydiving, helicopter, ballooning — have zero deals.** The
things worth travelling for are exactly the things this catalogue does not stock.
INFERRED, for Part C: the rule is sound *in production*, where live Groupon stocks
helicopter tours at 10–18 per city (§5e) — so it ships as a recommendation with the
threshold named, never as a prototype screen sized from this data.

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

### F3's exposure — retained deliberately, so stated rather than buried

VERIFIED: of F3's 321 dead ends, **only 6 have the answering deal in another
city**. 158 are in the user's own city and 157 are `can't tell`. That is what
withdrew the "geographic thinness" diagnosis (**§9 row 10**); the population, and
the class key `F3_geographic` that `query_classes.csv`, `web/mock/build.py` and
`002-recoverability` depend on, are unchanged.

**Its recoverability range was deliberately left unchanged at 25% (10–40%)** rather
than re-derived, because re-deriving it lowers the headline and the generous
number is the one worth defending. F3 contributes 12.9 of the 36.3 purchases — 36%
of the entire search-side estimate — so this is a live exposure, not a footnote.

### What this obliges the prototype to do

**Do not build a nice semantic search bar and call it done.** The largest bucket
(`nowhere`, 43.2% — band to 64.7%) is **unfixable by search**, and the most
interesting failure (F1) is **invisible to every search metric** because it
returns a full page. A prototype that only demos better matching has answered a
different question than the one asked. Behaviour per class: `001-part-b/SPEC.md`
§3/§4, which owns that contract in more detail.

---

## 8. How to quote the headline numbers

**Not a copy of the numbers — a copy is what drifts (§9 row 12).** Every figure
lives in its own section with its tag; go there. What this section carries is the
short list of numbers that come with a **rule about how to say them**, because
quoting those correctly is where Part C is most easily caught out.

| Number | The rule | Where |
|---|---|---|
| **52.5%** combined dead-end (29.3% zero + 23.2% at 1–2) | Lead with this, **not** 29.3%. Stopping at zero-results understates it by nearly half. **Do not widen it to 57.7%** — the 26+ tail was tested and rejected, see below | §1 |
| **81.2%** English vs **39.0%** local, gap **42.3pp** | Always as the matched pair with the gap. Loanwords for unstocked concepts fail at the ordinary 44.0% and are a *supply* story — never merge the two | §5b |
| **~12%** search-fixable (central 11.8%, range 5.6–15.1%) · **36 purchases/mo** | **Quote ~12%, never ~18%**; the ~18% / 59 figures are withdrawn (§9 row 7). Pair the percentage with the absolute | §5e |
| `nowhere` **43.2%** | **Never one end of the band [43.2%, 64.7%] alone** — the `plausible` seam moves 1,016 dead ends together and under one reading the ordering flips | §5f |
| **299** purchases / 30 days | An **upper bound, not a forecast**, at s2p 11.36%. Recovered demand converts worse than organic | §5 |
| **723 purchases** across 5 markets | The denominator for anything "per month": +36/mo is **+5.0%**; the supply-void ceiling of +271 is **+37.5%** | §5e |
| Typos **1.9%** (strict) or **7.5%** (long tail) | Name which definition, every time. Use 1.9% for "typos", 7.5% for "the long tail" | §4 |
| Funnel **38.1 / 29.8 / 11.4** | Over **non-zero** searches. Over all 8,997 it is CTR 27.0% / s2p 8.0%. Lowest market s2p is **FR**, not PL | §5 |
| corr(city deals, zero rate) **−0.379** | n=20 — report the **direction only**, and say n=20 | §3 |
| F3 "geographic" | A **withdrawn diagnosis**. Say "uneven across cities, cause not established" | §5f, §9 row 10 |
| `query_classes.csv` = **751** rows | — | §5d |

**The right-hand tail was tested and rejected — `INDEX.md` 6.6, CLOSED
2026-08-06. Do not widen the dead-end definition.** Plotting purchase rate
against the **exact** result count exposed a second collapse: searches returning
**26 or more** results convert at **2.3%** against **17.8%** at 4–25 (471
searches, 5.2% of all). Adding them would move the headline to 57.7%. **It does
not survive checking, and the reason is worth carrying into Part C**, because it
is the same test that *validates* the ≤2 rule:

| | lands in **1–2** results | lands in **26+** results |
|---|---|---|
| Predicted by the query? | **Yes** — χ² p = 4×10⁻¹⁶ | **No** — χ² p = 0.65 |
| By language | English 64.6% vs local 30.9% | 8.3% vs 7.3% |
| By market · city · coverage | varies | 6.8–8.2% · 4.5–10.0% · 6.5–8.1%, all flat |

Landing above 25 is **indistinguishable from a shared random draw** on every
dimension in the data. The paired test settles it: across the **123 market+query
pairs observed in both bands**, the *same* query converts at **18.3%** when it
lands 4–25 and **2.6%** when it lands 26+ (106 of 123 pairs lower, sign test
p = 6×10⁻²³). Nothing about the query changed, so the rate is a property of the
drawn count. Same status as the missing `3` in §0: a **generation artifact**,
stated rather than smoothed over. **52.5% stands; nothing credits the tail.**

**Mechanism note someone will re-derive, so state it first.** The language effect
runs mostly through the **1–2 band, not the zero band**: English and local
phrasings differ by only **8.1pp** on zero-rate but **42.3pp** on dead-end rate,
because English queries land in 1–2 on 64.6% of their non-zero searches against
30.9% for local. That is not a weakness in §5b — it is *consistent with F1*, a
query that returns a thin page of the wrong things rather than nothing at all.
Quote 42.3pp; if asked about zeros alone, the answer is 8.1pp **and this
paragraph**.

**Live-catalogue figures are a separate namespace — never mix them with the
above.** Live Groupon returns exactly 3 routinely (so the dataset's 0,1,2→4 gap is
a generation artifact); `paragliding`/London returns 2 cable-car river passes and
`kitesurf` a barista kit (silent substitution, *observed*); the API exposes no
relevance score or matched-term field; adrenaline is thin in London, Berlin and
Paris alike. Full statements and their limits: §5e. **No vendor-acquisition
recommendation for a named city follows from any of them.**

---

## 9. Corrections register — every claim made and then withdrawn

**The only record of retractions in the package.** Consolidated 2026-08-06 from
ten places across this file and `PLAN.md`; a new retraction is a new row here, not
a new paragraph elsewhere. Part C's tools log should be drawn from it.

The pattern across the twelve rows is itself a finding: **most are a coarse or
convenient measurement mistaken for a finding** — a category count standing in for
a title count, a UI bucket for an exact count, a multi-word count for supply, a
symptom for a cause. Every one was caught by measuring the same thing a second
way, never by re-reading the first result.

| # | Date | The claim, withdrawn | What killed it | What replaced it |
|---|---|---|---|---|
| 1 | 2026-08-05 | Skydiving is a **matcher failure**: the `activities` L2 category exists (132 deals), so search had stock and failed to find it. `validate.py` Layer 3's decisive table printed "MATCHER FAILURE" — the exact opposite of the truth | Re-running the test at **title** level instead of `category_l2` level. There are only five L2 categories, so a category-level test reports "the category exists" for concepts the catalogue stocks nothing of. `activities` holds only city tours, escape rooms and karting | **SUPPLY VOID in all five markets, 0 deals stocking adrenaline** (§3 Tier 2). The test now runs at title level throughout. **This is the tools-log example to use in Part C** — a plausible mapping produced a confidently inverted headline |
| 2 | 2026-08-05 | Search→purchase is "roughly 5–10% by market, **PL lowest**" | Re-running `validate.py`. Both halves were wrong — a wrong *directional* claim about a **named market** is precisely what "claims survive us checking them" catches | **7.0–9.0% over all searches; FR lowest, PL third** (§5). The stale CTR/CVR trio 38.4 / 30.0 / 11.5 was replaced at the same time by **38.1 / 29.8 / 11.4** |
| 3 | 2026-08-05 | Live GB does **silent token-dropping**, and `shark diving`'s 80+ results "came entirely from *diving*". Separately: a real-but-unstocked word **widens** the result set, as a property of the query semantics | Exact `totalCount`s. `diving` alone is **29**, and dropping a token cannot *raise* a count. And `dinosaur` has **13** matches of its own, so "widens" was overreach — the arithmetic fits neither a union nor an intersection (`massage` 458 + `dinosaur` 13 → 460, not 471; `shark` 10 + `diving` 29 → **81**, not 39) | **"Adding a term does not reliably narrow."** Consistent with scored retrieval over a relevance threshold plus an expansion stage, tuned per market — and the ranker config is not observable from outside, so it is not guessed at. Derivation: `PLAN.md` §4 Finding 1 |
| 4 | 2026-08-05 | The DE Zittau session was **inconsistent**: it served Thai massage 75–79 km away yet returned zero for `fallschirmspringen`, implying a radius bug | It was an inference, not an observation. A finite maximum radius with **no German skydiving inside it** produces the identical result with no inconsistency at all — and whether skydiving supply exists near Zittau was never checked | Only what the screenshot shows plainly: **the zero state blames filters the user has not applied** ("Versuchen Sie, einen der angewendeten Filter zu entfernen", with no filters applied). `PLAN.md` §4 Finding 3 |
| 5 | 2026-08-05 | Polish diacritics cost **4× recall** — read off the UI labels "40+" vs "10+" | Exact counts with `division` pinned to `warszawa`: **162 vs 95**. The UI buckets were coarse **and** the two runs had an unpinned location. Both the ratio and the framing were wrong | Single-token loss is small (`masaż` 272 / `masaz` 248, **−8.8%**); the penalty lands on **multi-word** queries (−41%, −48%). Sharper and more actionable, because it says *where* to fix it. `PLAN.md` §4 Finding 4. Later narrowed again live — the effect is specific to the `masaż` token family (§5e) |
| 6 | 2026-08-06 | Upper bound of **~303 purchases** over 30 days, at "the observed 11.5%" s2p | The 11.5% was stale — it sat **eleven lines below the same section's own 11.4%**. A stale rate inside a *derived* figure, so the bound had to be recomputed rather than the digit edited | **299 purchases** at s2p **11.36%** (§5). It had already propagated into the Part B spec's acquisition-brief copy — which is how a drifted rate becomes a claim in the deliverable |
| 7 | 2026-08-06 | **F5 = "ranking cutoff"**, and its recoverability, resting entirely on the dataset anomaly that no search ever returns exactly 3 results | **Self-caught, on the supplied data.** The diagnosis was an inference *from an absence* with a competing explanation — the generator — that this file cannot rule out. Unattributable, therefore not a basis for a 40% point estimate. *(The live catalogue then corroborated the generator branch: Groupon returns exactly 3 routinely — `quadbike` 3, `trapeze` 3, GB · london, N=33, smooth distribution 0(×6), 1(×4), 2(×2), **3(×2)**, 5, 6, 7, 8, 10, 17. §1. Corroboration, not basis — the withdrawal stands without it.)* | The **population survives, the diagnosis does not**: 73 pairs / 658 searches still counted, relabelled a **second unexplained residual** alongside BASELINE. Recoverability withdrawn to **zero**, not re-estimated — which moved `002-recoverability` from **59 → 36 purchases/mo** and search's share from **17.9% → 11.8%**. Quote ~12%, never ~18% |
| 8 | 2026-08-06 | Live London **stocks adrenaline abundantly** — on the strength of `hot air balloon` **558** and `wing walking` **449** | Those are **multi-word** queries, and the same section establishes that multi-word counts are inflated by fragment matching. The evidence for "abundant" was an artifact of the very defect being described. Single-token probes in **Berlin and Paris** exposed it | **Thin in production too, but not absent** — skydiving 2/3/3, ballooning-paragliding 2/1/0, helicopter 11/10/18 (London/Berlin/Paris), §5e. Part C may say the pattern is not merely a synthetic artifact; it may **not** put a number on real Groupon's gap. **The sharpest tools-log entry in the package**: one probe contradicted another *in the same session*, and only a second and third city surfaced it |
| 9 | 2026-08-06 | "Live GB stocks **300+** helicopter tours" — the caveat separating the live catalogue from the dataset in `PLAN.md` §4 | The single-token exact count is **11** (`helicopter`, division `london`, 2026-08-06; `003-live-validation/RESULT.md`). **300+ was a coarse UI bucket or a multi-word count** — the precise artifact class that `PLAN.md` §4's own method paragraph says the exact-count harness exists to catch. The file was caught by its own stated method | **`helicopter` 11 (London) / 10 (Berlin) / 18 (Paris)** — the same single-token figures as row 8. The live/synthetic separation the caveat was drawing still holds; the number it was drawn with did not |
| 10 | 2026-08-06 | **F3 = "geographic thinness"** — and the user-facing copy it justified, *"We have this, just not in your city."*, **shipped and live in `explainer.html`** where a grader could click a chip and read it | A direct test of where the inventory actually sat: of F3's **321** dead ends, **only 6** have the answering deal in another city — 158 same-city, 157 can't-tell. `classify.py` assigns F3 from **city-to-city variance in dead rate** (`city_spread >= 0.25`), which is a *symptom*, not a location. The name was never earned, and the copy was **false for 315 of 321 rows** | Relabelled **"Uneven across cities"**; class key `F3_geographic` deliberately unchanged so `query_classes.csv`, `web/mock/build.py` and `002-recoverability` keep working. Copy fixed 2026-08-06. **Recoverability deliberately left at 25% (10–40%)** rather than re-derived — F3 is 12.9 of the 36.3 purchases, so §5f states the exposure instead of hiding it |
| 11 | 2026-08-06 | §5f's first draft, which **mixed a mapped-only denominator with a total one** across its own bucket table | Recomputing every bucket over one denominator. The four buckets have to sum to the dead-end total, and they did not | **All 4,720 dead ends, one denominator throughout** (§5f). A per-row assertion in `classify.py` now fails the build if the four columns stop summing to `deads` |
| 13 | 2026-08-06 | The **26+ result tail** (471 searches converting at 2.3% vs 17.8%) is the **silent-mismatch class showing up at the top of the distribution** — "the queries concentrated there are overwhelmingly concepts this catalogue stocks nowhere" — and therefore **52.5% is an understatement**. Written into `INDEX.md` 6.6, §8 here, and the built `explainer.html` before it was tested | Two independent checks, both of which the original inference had skipped. **(a)** The `sushi/brunch/paintball` concentration was an artifact of counting `raw_query` **without grouping by market**; grouped, the top pairs are `facial`, `sports massage`, `coloration`, `gym` — mainstream **stocked** concepts. Coverage mix in the tail (56.1/23.4/20.6 stocked/plausible/absent) is **indistinguishable** from 4–25 (54.7/26.7/18.6). **(b)** A first structure test said "random" for *both* bands — but it was restricted to pairs with n ≥ 10, which **excluded every English query**. Re-run without the cutoff, the two bands separate: 1–2 is **structured** (p = 4×10⁻¹⁶), 26+ is **not** (p = 0.65) | **A generation artifact — 6.6 CLOSED, the tail credited nowhere, 52.5% unchanged.** The paired test is the replacement claim: the same market+query converts at **18.3%** in 4–25 and **2.6%** in 26+ across 123 pairs (p = 6×10⁻²³), so the rate belongs to the drawn count, not the query. §8. The same test *validates* the ≤2 rule, which is the useful half |
| 12 | 2026-08-06 | `outputs/query_classes.csv` holds **755** market+query pairs (§5d prose) | Counting the CSV: **751** data rows. §5d's own class table had always summed to 751 (178+161+259+73+15+65), and `001-part-b/SPEC.md` §2 had it right — only the prose drifted | **751**. Copying numbers into a quote-card is the channel that produced this drift, so §8 was rebuilt from a list of reproduced figures into a table of **quoting rules** that points at the owning section instead |
