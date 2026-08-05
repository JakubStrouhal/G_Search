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

VERIFIED ANOMALY: **no search anywhere returns exactly 3 results.** The
distribution runs 0, 1, 2, then jumps to 4. This is either a ranking cut-off
or a data-generation artifact. CANNOT VERIFY which from this file. State it
openly — it is a flag on the data, and noticing it is worth more than
pretending the distribution is smooth.

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

CORRECTION TO AN EARLIER PASS: `validate.py` Layer 3 maps adrenaline →
`activities` L2 and therefore prints "MATCHER FAILURE" for adrenaline. **That
verdict is wrong** — it is an artifact of my crude concept map, because
`activities` exists but holds none of the requested inventory. Fix the map
before quoting that table. Left in deliberately so you can see the failure
mode: a category that exists is not a category that stocks the thing.

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

VERIFIED: all query pairs with n ≤ 3 (the typo tail: `raftng`, `raffting`,
`fallschirmspringn`, `heißluftballon fahrt` misspellings) account for **198
zero-result searches, 7.5% of all zeros.** And 73 of those 198 are adrenaline
concepts — i.e. they would return nothing even spelled perfectly.

VERIFIED further: most typos already return results. DE `sprtmassage`,
`thi massage`, `neckenmassage`, `ruckenmassage` all return results at 0% zero
rate. **The matcher is already fuzzy on spelling.**

So spell-correction is worth roughly **125 searches out of 2,633 zeros (4.7%)**.
Do not build the prototype around it. Mentioning it as a cheap win is fine;
leading with it would be a misread.

---

## 5. Funnel baseline (for sizing anything)

VERIFIED, non-zero searches only:
- CTR 38.4%, click→purchase 30.0%, search→purchase 11.5%.
- By market s2p: roughly 5–10%, PL lowest.

VERIFIED upper bound: if all 2,633 zero-result searches converted at the
observed 11.5%, that is ~303 purchases over 30 days across 5 markets.
**Label this an upper bound, not a forecast.** Recovered demand converts worse
than organic demand. If you present it any other way you have failed the
"claims survive their data checks" criterion.

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

- [ ] Re-run `validate.py`; confirm every number above.
- [ ] Fix the adrenaline → `activities` concept mapping (see §3 correction).
- [ ] Extend the concept map until the "unmapped" bucket is small. It is
      currently 3,806 searches / 883 zeros — too big to ignore. Note that
      `paracaidismo`, `paseo en globo`, `vol en montgolfiere`, `lot balonem`,
      `skoki spadochronowe`, `lot helikopterem` sit in it and are all
      adrenaline; adding them moves the adrenaline share up.
- [ ] Decide and state the position on the missing `results_shown = 3`.
- [ ] Decide and state the position on whether paintball's healthy conversion
      is substitution or a data artifact.
- [ ] Log hours and AI tools used, including what the tools got wrong. The
      adrenaline/activities misclassification in §3 is a real example — use it.

---

## 8. Facts to reuse verbatim

- 8,997 searches · 613 unique queries · 568 deals · 75 unique deal titles ·
  5 markets · 4 cities each · June 2026.
- 29.3% zero results. 23.2% return 1–2 results. 52.5% combined dead-end.
- Zero-result split: 64.2% always-zero (supply void), 35.8% intermittent.
- Adrenaline = 47.6% of all zero-result searches.
- Inventory: 4 L1 categories, 5 L2 categories, no aerial/water/motorsport.
- corr(city deal count, zero rate) = -0.379, n=20.
- Typo tail = 7.5% of zeros, and most typos already resolve.
