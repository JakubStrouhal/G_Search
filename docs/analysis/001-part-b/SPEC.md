---
created: 2026-08-06
updated: 2026-08-06
note: F3 and F5 diagnoses withdrawn and the behaviours re-grounded; four-bucket vocabulary added; duplicated defect text replaced with INDEX citations.
---

# Part B — build spec

Groupon case study R29944 · discovery prototype. **This file is the build contract for Part B —
build from it only.** `INDEX.md` owns its status. Supersedes `BUILD_SPEC.md` (draft) and
`SPEC_REVIEW.md` (its review), both in `archive/`; the review's six open decisions **D1–D6 are
resolved here** — see §11.

**Read `docs/analysis/FINDINGS.md` first.** Every behaviour below exists because of a specific
verified finding. If a feature can't be traced to one, it isn't in scope.

**The brief's actual test:** handle every query type found in Part A *including the unfixable ones*.
What it does when it has no good answer tells them as much as what it does when it succeeds. Code
quality, visual design and authorship are explicitly not graded.

**The one-sentence thesis the build must prove:** this is not a search-quality problem, it is a
marketplace liquidity problem that search is merely measuring. The prototype is the instrument that
makes that visible.

---

## 1. Scope — locked

| Priority | Component | Why |
|---|---|---|
| **MUST** | Failure classes behave visibly differently | This *is* the finding. Without it the demo is a search bar. |
| **MUST** | Staff panel ("show your working") | Highest-value component for this audience. The literal answer to "show your working". |
| **HIGH** | Demand-capture loop + simulated acquisition brief | Maps to Groupon's named international growth driver: supply expansion. |
| **NICE** | Natural-language query input | Rides on the embedding already required. |
| **CUT** | Returning-customer recommendations | No user IDs, sessions or purchase history. Building it means fabricating evidence — the exact failure being tested for. |
| **CUT** | Real autonomous vendor-outreach agent | Simulate it. The idea scores; the plumbing does not. |
| **CUT** | Two personas | A control that changes only copy, needing a Part C caveat, in an exercise where honesty is graded. |
| **CUT** | "Make it look like Groupon" | Visual design is explicitly not assessed. Cut, not deferred. |

---

## 2. Tier assignment comes from Part A, not from a threshold — **D1, D4**

The draft separated Tier 1 (paintball) from Tier 2 (skydiving) with a single similarity threshold.
Both have zero matching inventory, and against a catalogue of city tours, escape rooms, karting,
fitness, beauty, dining and massage there is **no principled reason paintball scores above `LOW` and
skydiving below it** — karting may sit closer to skydiving's thrill vector. The demo script depended
on an ordering nothing guaranteed. This is also the grading criterion *"the prototype reflects the
analysis rather than being a nice search UI bolted on beside it"*: make the link mechanical.

**Resolution — the contract already exists.** `docs/analysis/outputs/query_classes.csv` is 751
market+query rows with `failure_class`, `concept`, `searches`, `zeros`, `deads`, `city_spread`,
`coverage`, `deals_stocking`, `is_english`. So:

- **`query_classes.csv` assigns the class.** Deterministic, traceable to Part A, immune to the
  ordering problem. This is a `fetch()`, not new work.
- **Thresholds set presentation confidence *within* the class.** Still the interesting product
  mechanic, still worth demoing, no longer load-bearing for the demo script.
- **The staff panel shows both**, so a grader sees agreement — or disagreement, which is honest and
  more interesting than either alone.

**Unknown queries** (not in the CSV) fall back to the threshold path. Say so in the staff panel.

---

## 3. Required behaviour per class

**Two cuts of one population, and the prototype speaks both.** *Where was the answer?* assigns the
owner; F1–F6 assigns the mechanism. Over all 4,720 dead ends (`FINDINGS.md` §5f):

| Where the answer was | dead ends | share | owner |
|---|---|---|---|
| **Nowhere in the market** | 2,039 | 43.2% | Merchant acquisition — not search |
| **The user's own city** | 1,520 | 32.2% | Search. The search problem's real size |
| **Another city in the market** | 145 | 3.1% | Product/UX |
| **Can't tell from this catalogue** | 1,016 | 21.5% | Not attributed |

**They nest, and in the default reading the nesting is an identity:** `nowhere` **is** F1 ∪ F4
(455 + 1,584); `same_city` is BASELINE 929 + F5 236 + F2 197 + F3 158 — asserted per row in
`classify.py`, which fails if the four columns stop summing to `deads`. Same mechanical
analysis→build link as §2. **Under the other two seams the membership itself moves**, not just the
counts: BASELINE's 514 and F3's 157 can't-tell dead ends land in `nowhere`. Every per-class bucket
number below is the default reading.

**Never quote one end of the `nowhere` band [43.2%, 64.7%] alone**, in UI copy or in Part C: all
1,016 `can't tell` dead ends move together on one judgement (`PLAUSIBLE_COUNTS_AS`), and under the
reading that credits a generic deal **same-city overtakes nowhere, 48.9% vs 46.8%**. Per-row bucket
counts (`dead_nowhere / dead_same_city / dead_another_city / dead_cant_tell`, already columns on
`query_classes.csv`, which loads as a table — §6) go in the **staff panel** beside that caveat,
never in user-facing copy.

### F1 — Silent substitution (259 pairs, 1,326 searches) · the invisible failure

**Evidence:** `FINDINGS.md` §3 Tier 1 (sizing — tagged CANNOT VERIFY: a coverage gap, not a
measurement of harm) and §5e (the mechanism). Buckets: 455 of its 527 dead ends `nowhere`, 72
can't-tell.

**Behaviour.** Below the similarity floor the system stops presenting results as *the answer*.
Header changes from "Results for X" to **"We don't have X — you might also like"**. Same deals,
honest frame. **Name the token that could not be matched** before showing alternatives.

Put `458 = 458` on the screen and in the staff panel — live **result counts**, not scores:
`xqzjw massage` returned 458 results and so did `massage`; `xqzjw masaz` 248 = `masaz` 248; `xqzjw`
alone 0. A zero-match token is *exactly inert*. **Tag it live-catalogue evidence** (§5e): in
production the matcher matches fragments and the user has no lever. That this dataset does the same
stays inference.

> **The nth-order point — demo this explicitly.** The obvious fix, loosening matching to cut
> zero-results, makes this tier *worse*. The dashboard goes green while trust goes down.

### F4 — Supply void (178 pairs, 1,689 searches) · search cannot fix this

**Two rules, two counts — 185 / 1,691 (`validate.py`) against 178 / 1,689 (`classify.py`, which is
what `query_classes.csv` and so the prototype use). A definition, not an error**, reconciled in
`INDEX.md` known issue #6. **Quote per-cell counts** (GB helicopter tour 100/100/0): directly
computed, identical under both rules. No aggregate pair count in UI copy.

**Evidence:** `FINDINGS.md` §3 Tier 2, §5d. Buckets: 1,584 of its 1,684 dead ends `nowhere`, 100
can't-tell — the largest single contributor to the merchant-acquisition bucket by a wide margin.

**Behaviour, in value order:**
1. **Name the gap honestly** — "No skydiving in Berlin yet."
2. **Capture intent.** Notify-me writes market + city + concept to the demand table. One event
   serves the user *and* merchant acquisition.
3. **Offer adjacency, clearly labelled** — "Closest thrill we do stock: karting." The label is what
   separates this from F1. Deliberate friction where the stakes demand engagement.
4. **Cross-city is data-gated, never a default** — offered only where that row's
   `dead_another_city > 0`. For this class it is **0 on every row**, by construction: a concept
   absent from the market is stocked in none of its cities. Say so rather than skipping it silently.
5. **Show demand back** — "37 people searched this in Berlin last month." **Real number** (§5).

### F2 — Lexical/morphological miss (65 pairs, 358 searches)

**Evidence:** `FINDINGS.md` §5b — English phrasing dead-ends at **81.2%** against **39.0%** local,
42.3pp across 47 of 48 matched pairs, both confounds killed. The live diacritic penalty (§5e)
**replicates but does not generalise** — it is specific to the `masaż` token family, so no copy may
promise it everywhere. Buckets: 197 of its 280 dead ends `same_city`.

**Behaviour.** `masaż tajski`, `masaz tajski`, `thai massage`, `massage thai` all hit the same
deals. **Show that it did** — display the normalisation that fired.

### F3 — Uneven across cities (15 pairs, 645 searches) · diagnosis withdrawn, population kept

**"Geographic thinness" was never earned.** `classify.py` assigns this class from city-to-city
variance in dead *rate* (`city_spread >= 0.25`) — a symptom, not a location. Tested against
inventory: **only 6 of its 321 dead ends have the answering deal in another city**; 158 same-city,
157 can't-tell (`FINDINGS.md` §5f, `INDEX.md` #12). Take the explainer's label, **"Uneven across
cities"**; the key `F3_geographic` stays so `query_classes.csv` and `002-recoverability` keep working.

**Withdrawn — the copy.** *"We have this, just not in your city"* and *"20 in Kraków, 90 minutes
away"* were **false for 315 of 321 dead ends** and must not ship. Nothing may imply the answer sits
one city over unless that row's `dead_another_city > 0` — a gate whose whole market-wide population
is 145 dead ends (3.1%), topped by BASELINE and F5 rows, not F3, and composed of hair, karting, gym
and nails. Nobody drives to the next city for a haircut: keep it small, never a demo headline.

**Retained deliberately — the population and the 25% (10–40%) recoverability range**, not
re-derived, because re-deriving lowers the headline and the generous figure is the published one.
Say the exposure rather than hide it: F3 is **12.9 of the 36.3 purchases/month, 36% of the whole
search-side estimate**, and the tightened alternatives (**7.8%**, then **5.7%**) are published
beside it (`INDEX.md` #12).

**Behaviour.** Say only what is established: *stocked in your city, and failing here far more than
one city over — we cannot say why.* No location claim, no radius offer by default. Shares the
stocked-and-unexplained path with F5 and BASELINE (§10 step 5); the class and its bucket split stay
visible in the staff panel.

### F5 — Unexplained residual (73 pairs, 658 searches) · the second one

**"Ranking cutoff" is dead, on the supplied data's own terms.** It rested entirely on "no query
returns exactly 3" — an inference from an absence that the supplied data cannot attribute between a
cutoff and the generator. Unattributable, so withdrawn rather than re-estimated (`FINDINGS.md` §1).
*(Live corroborates the generator branch — Groupon returns exactly 3 routinely, `quadbike`,
`trapeze`, `003-live-validation/RESULT.md` P4 — but the withdrawal does not depend on it.)*
`classify.py` assigns F5 as a
**residual** — stocked, failing, not F2, not F3 — so it is a second BASELINE, not a cause.
Recoverability was withdrawn to **0**, not re-estimated: `002-recoverability`'s central estimate
moved 59 → **36 purchases/month**, 17.9% → **11.8%**.

**The behaviour survives on a different footing. Treat 1–2 results as a near-empty state, not a
results page.** The justification is the §1 cliff, not a ranking theory: 1–2 results convert at
**1.7% s2p** against 16.1% at 4+ — like zero — and that holds in 137 of 138 concept × city strata.
So it is a **result-count rule**, firing wherever the count is 1–2 whatever class the row carries.
Degrade gracefully rather than snapping to zero.

### F6 — Intent-type confusion · **cut, and stated as cut**

**Evidence:** live only — `shark` returns 10 results, all shark blankets, socks and water pistols
(`FINDINGS.md` §5e). **Cut because** this catalogue contains no Goods, so the class cannot occur in
the dataset. It stays in the coverage table (§4) marked cut with this reason: a grader checks for it
in ten seconds, and silent absence reads as not having noticed.

### BASELINE (161 pairs, 4,321 searches) · the uncomfortable residual

Queries the catalogue plausibly covers that still dead-end ~40% of the time. Not a named failure
class — it is what is left after the six, and it is the largest bucket by volume. **Since F5's
withdrawal there are two such buckets:** of the 1,520 same-city dead ends, **1,165 are unexplained**
(BASELINE 929 + F5 236) against 355 with a named mechanism (F2 197 + F3 158) — which is exactly why
the defensible search-side fix is 11.8%, not 32.2% (`FINDINGS.md` §5f). No fix is claimed for
either. **State it in Part C**; a taxonomy that accounts for everything has been fitted.

---

## 4. The coverage table — a required deliverable

The brief's hard requirement is "every query type found in Part A, **including the ones you cannot
fix**." Ship this table in the prototype itself, not just in Part C.

| Part A class | Pairs / searches | Prototype behaviour | Demo query | Fixable by search? |
|---|---|---|---|---|
| **F1** silent substitution | 259 / 1,326 | Name the unmatched token; reframe as labelled adjacency | `paintball` (GB) | Partly — needs term-constraining |
| **F2** lexical/morphological | 65 / 358 | Normalise; show the normalisation | `masaz tajski` (PL) | **Yes** — the genuinely fixable layer |
| **F3** uneven across cities | 15 / 645 | Name the unevenness; no location claim; cross-city only where the row shows one | `manicura` (ES) | Unknown — the mechanism was never shown |
| **F4** supply void | 178 / 1,689 | Honest empty state + intent capture + acquisition feed | `fallschirmspringen` (DE) | **No** — merchant acquisition |
| **F5** unexplained residual | 73 / 658 | Treat 1–2 results as near-empty (a result-count rule) | 1–2 result case (§7 #2) | Unknown — no cause established |
| **F6** intent-type confusion | live only | — | — | **Cut:** no Goods in this catalogue |
| BASELINE residual | 161 / 4,321 | No claim made | — | Unexplained — stated, not fixed |

Ship the *where was the answer?* cut (§3) beside it; say they nest. **F3's demo query changed** from
`crossfit` (FR) — whose 27 dead ends are *all* can't-tell, so it could never have demoed a location
claim — to `manicura` (ES): 45 searches, 21 dead ends, **all 21 same-city**, stocked, failing in
Madrid (15 of 26) far more than in Valencia (2 of 8), in the one market the demo script does not
already use.

---

## 5. The demand loop

```
abstention event → demand table (market, city, concept, query, count, date)
                 → aggregate by market × city × concept
                 → mocked acquisition brief
```

**Seed the table from `search_log.csv`.** The draft built it only from runtime events, so a fresh
demo would show "1 search". The real numbers already exist:

| Cell | Adrenaline searches | Deals stocking |
|---|---|---|
| GB · London | 222 | 0 |
| FR · Paris | 167 | 0 |
| ES · Madrid | 162 | 0 |
| DE · Berlin | 131 | 0 |
| DE · Berlin · `fallschirmspringen` | 37 | 0 |

Grader clicks then increment a real baseline. Seeding is also the more honest artifact.

**Brief output:** "Berlin · skydiving · 37 searches · 0 deals · est. lost purchases ≈ 4/month
(upper bound) · suggested vendor outreach list."

**Compute the lost-purchase figure, never hard-code it.** Use **s2p = 11.4%** (recomputed
2026-08-06 from the CSVs: on searches that returned results, CTR 38.14% / click→purchase 29.79% /
s2p 11.36%). Label it an **upper bound**, never a forecast — recovered searches convert worse than
organic ones.

**Simulate the agent.** A function that reads the table and renders the brief. Do not build
outreach. The demand table *is* the merchant acquisition feed — the differentiating claim, sitting
exactly where Groupon's two stated priorities intersect.

---

## 6. Architecture

### Index time — the highest-leverage decision

**Do not embed the deal title.** 568 deals share only 75 unique titles and they are generic
("Sesja Wellness", "Wellness-Massage Paket"). Embedding those gets you nothing.

**Hand-write 75 short service descriptions — do not LLM-enrich them. (D2)** The failure mode is
specific and fatal: if enrichment writes "outdoor adventure, adrenaline, thrills" onto the
`activities` deals, skydiving clears `LOW`, **F4 collapses into F1, and the demo's central finding
becomes an artifact of generated text.** There are only 75. Hand-writing is cheaper than building
and auditing an enrichment pass, defensible line by line in Part C, and consistent with why the
concept maps were hand-built. Commit the file; show the matched document in the staff panel.

Embed `title + category_l1 + category_l2 + city + market + hand-written description`.

### Query time

- **Multilingual sentence embedding of the raw query. No translation layer** — translation is
  brittle on slang and typos and adds a failure point. A multilingual model puts `masaż` and
  `massage` in nearly the same coordinate; language stops mattering.
- Cosine similarity against the market's inventory.
- *(Production only — state in Part C, do not build:)* BM25 lexical + dense vectors fused via
  reciprocal rank fusion, cross-encoder re-rank of top 50.

### The abstention threshold

A vector search **always** returns k neighbours; cosine is never zero. A naive implementation
therefore **eliminates zero-result searches and maximises silent mismatch** — the metric looks
perfect and the product gets worse.

```
max_similarity >= HIGH   → confident results ("Results for X")
LOW <= max_sim <  HIGH   → labelled adjacency ("We don't have X, but…")
max_similarity <  LOW    → honest empty state + intent capture
```

**Calibrate against the labelled set Part A already emits, not against two anchor cases.**

**The ground truth is `coverage`, and it is bigger and cleaner than this section previously said.**
Checked against `query_classes.csv` (751 rows, 2026-08-06):

| `coverage` | rows | what it means | correct system behaviour |
|---|---|---|---|
| `absent` | **437** | the market stocks nothing for this concept | **must fall below LOW** — abstain |
| `plausible` / `stocked` | 314 | the market stocks something | must clear LOW |

`absent` decomposes **exactly** into `F4_supply_void` **178** + `F1_silent_substitution` **259**,
with no leakage in either direction (`F4 ⊂ absent`, `absent − F4 = F1`). That is the same partition
as the spine's `nowhere` bucket, which `FINDINGS.md` §5f asserts in code as F1 ∪ F4.

**This corrects an error in the previous wording of this paragraph,** which described the 178 F4
pairs as "`coverage == 'absent'`". They are a *subset* of it. Calibrating on 178 would have trained
the threshold to abstain on supply voids while **passing all 259 silent-substitution rows** — the
single failure the whole prototype exists to fix. The correct target is all **437**.

Sweep HIGH/LOW over the 437 / 314 split and **report the error rate, both directions separately**:
false-confident (an `absent` row clearing LOW) is the expensive one and is the F1 failure mode;
false-abstain (a `stocked` row falling below LOW) is the cheap one. "Thresholds calibrated against
751 labelled pairs from Part A, X% false-confident, Y% false-abstain, here are the failures" is
*evidence*; hand-tuning two scalars against two cases is fitting, and Part C would have to confess
it. This sweep doubles as the verification that §2's ordering concern is real.

**If the sweep cannot separate 437 from 314 at any (HIGH, LOW), stop and say so** — that result
would mean §1's MUST ("failure classes behave visibly differently") is unreachable by threshold
alone, and every screen built on it would be built on sand. Report it rather than tuning until it
looks right.

**Knowing when to return nothing is the product requirement, not an edge case.** Every abstention
writes a demand row.

### Stack — Supabase + Vue3, DB–BE–FE (D3, **reversed 2026-08-06 by the owner**)

This is built as a software product, not a demo bundle.

| Layer | What | Holds |
|---|---|---|
| **DB** | Supabase Postgres + `pgvector` | `deals`, `deal_documents` (title + categories + city + hand-written description), `embeddings`, `query_classes` (the Part A contract), `demand_events` |
| **BE** | Supabase — SQL views, RPC for the search call, RLS | Similarity search, threshold banding, demand writes. **Keys and any model calls live here, never in the browser.** |
| **FE** | Vue 3 | The class-specific screens, staff panel, acquisition brief, coverage table |

- **Precompute embeddings offline, load once.** No model latency while a hiring manager clicks, no
  keys in the front end. The FE reads; the only write path is `demand_events`.
- **Seed `demand_events` from `search_log.csv`** at migration time (§5), so a fresh instance shows
  real baselines rather than "1 search".
- **`query_classes.csv` loads as a table**, so the analysis→build link stays mechanical (§2).

**The budget tension, stated rather than hidden.** Phase 4 budgets **3–5 h**; Supabase + pgvector +
an offline embedding pipeline + Vue3 screens + staff panel + brief view is realistically **15–20 h**,
and output-per-hour is graded while more hours is explicitly *not* a better score. The owner's call
is that the product is worth the hours. **Log the real hours** — the brief requires it, and an
honest 18-hour log beats a fictional 5-hour one.

**The Part C line, adjusted.** The original restraint argument ("at 568 deals, pgvector inside
Postgres isn't just sufficient, it's *correct* — the catalogue is already relational and a second
specialist system would be operational overhead at this scale") still holds and should be made.
What cannot be claimed any more is that the whole system was sized down to the dataset. Say
instead: the stack is the one this would actually ship on, and name what it would cost at Groupon's
real scale.

---

## 7. Demo script — five queries (D5)

| # | Query | Market | Expected behaviour | Point made |
|---|---|---|---|---|
| 1 | `masaz tajski` | PL | Confident results; normalisation shown | F2: cross-lingual and diacritic matching works |
| 2 | a 1–2 result query | any | **Near-empty state, not a results page** | **The headline: 1–2 converts like zero. 52.5% dead-end, not 29.3%** |
| 3 | `paintball` | GB | **Labelled adjacency**, not a full page | F1: the invisible failure, made visible |
| 4 | `fallschirmspringen` | DE | Honest empty state + notify-me + demand row | F4: search cannot fix supply |
| 5 | Staff view on #4 → acquisition brief | — | Demand table → vendor brief | The loop closes on the supply side |

Optional 6th: natural-language input — "I'm in London four days with my family, what can we do?"

**Demo #2 replaces the draft's `masaż`-in-GB/London scenario** — reasoning in D5 (§11).

---

## 8. Staff panel — the spine of the demo

A persistent "Groupon staff view" button. For the query just run, shows:

- Raw query, detected language, market/city context
- The embedding match: top 5 deals with cosine scores, and the matched *document*
- Which threshold band fired, and why
- **Which F-class `query_classes.csv` assigns, and whether the threshold agrees** (§2)
- **Where the answer was for this row** — the four bucket counts off `query_classes.csv`, with §3's
  band caveat beside them. The only place a per-row bucket number appears.
- Whether a demand-table row was written
- **What today's system would have shown** — a full page of N results — side by side with what this
  shows. The most persuasive single artifact for the F1 claim, and nearly free.
- **What the system does not know** — "the log records a result count only, no query→deal mapping,
  so substitution is inferred"

Build the demo so the panel is worth opening on every single query.

---

## 9. Honesty register — carry into Part C

- **No query→deal mapping in the log** — only a count. F1 substitution is INFERRED from the
  catalogue. Cannot distinguish happy substitution from a generator ignoring relevance.
- **No search returns exactly 3 results — settled as a generation artifact, and only against the
  live catalogue**, which returns 3 routinely (`FINDINGS.md` §1). Evidence about the generator, not
  about the supplied data. Still open: whether paintball's healthy conversion is substitution or
  artifact (`INDEX.md` #4).
- **Two class names withdrawn, both populations kept** — F5 "ranking cutoff" (unattributable on the
  supplied data; live P4 corroborates) and F3
  "geographic thinness" (6 of 321). Both are residuals with no established cause, a smaller claim
  than each replaced. F3's 25% range is retained un-re-derived, with 7.8% / 5.7% published beside it.
- **The `nowhere` share is a band, [43.2%, 64.7%]** — one judgement moves 1,016 dead ends and flips
  the ordering (`INDEX.md` #13). Never quote one end. Two errors of opposite sign, held not netted:
  title matching inflates `same_city`, the `plausible` seam inflates `nowhere`.
- **No session IDs, no order values.** No repeat-search, abandonment or revenue analysis possible.
- **Data is clean enough to be synthetic.** Say so, and name the four things to instrument in week
  one: query→results mapping, null-result events carrying the raw query, session IDs, ranker
  relevance scores.
- **Thresholds are calibrated against Part A's labelled pairs, not learned**, and the error rate is
  reported rather than hidden.
- **Recovery estimates are upper bounds.** The all-zeros recovery bound is **299 purchases**
  (2,633 zero-result searches × 11.36% s2p), recomputed 2026-08-06.
- **The BASELINE residual is unexplained** — 4,321 searches, ~40% dead, no fix claimed.
- **The two concept maps disagree on the adrenaline share**, 59.9% against 47.6% (`INDEX.md` known
  issue #1). **Do not put an adrenaline share in UI copy**; quote per-cell counts, which are
  directly computed and identical under both.
- **Three cuts over one population, not three findings.** `FINDINGS.md`'s three tiers (64.2% supply
  void / 35.8% intermittent), this spec's F1–F6 — which dissolves "intermittent" into F2 + F3 + F5
  — and the four buckets of §3, which nest into F1–F6 as an identity. Three views of the same 4,720
  dead ends. Part C must say so explicitly, or a grader reading any two sees a contradiction.
- **The classifier's concept map misfires on typo'd queries** (`INDEX.md` known issue #8). Every
  affected row is n=1, so no headline moves — but the staff panel displays the concept, so it would
  show a visibly wrong one. Either fix the map or exclude `thin_n` rows from the panel.

---

## 10. Build order

1. Supabase project + migrations: `deals`, `deal_documents`, `embeddings` (pgvector),
   `query_classes`, `demand_events`. Seed from `deals.csv` and `query_classes.csv`. The stage, not
   the play.
2. Hand-write the 75 service descriptions. Commit the file.
3. Offline: build documents → embed → load vectors into Postgres.
4. **Sweep HIGH/LOW against Part A's labelled pairs; report the error rate.** Get the three bands
   right — and know how wrong they are — before touching UI.
5. Vue3 screens **by behaviour, not one per class**: confident results with the normalisation shown
   (F2), labelled adjacency (F1), honest empty state + capture (F4), near-empty (any row returning
   1–2). **F3, F5 and BASELINE collapse into one stocked-and-unexplained path** — with its diagnosis
   withdrawn F3 no longer earns a bespoke radius-widening screen, which takes a screen off the §6
   budget. Both classes stay visible in the staff panel and the §4 table, so nothing is hidden.
6. `demand_events` seeded from `search_log.csv` + notify-me writes via RPC.
7. Staff panel, including the side-by-side.
8. Acquisition brief view.
9. Coverage table (§4) as a visible page.
10. Deploy; test the five demo queries end to end.

Log hours as you go — per-hour productivity is assessed, and the log is a required deliverable
alongside AI tools used and what they got wrong.

---

## 11. Decision log — D1–D6 resolved 2026-08-06

| # | Question | Resolution | Why |
|---|---|---|---|
| **D1** | Does the threshold separate paintball from skydiving? | **Moot — `query_classes.csv` assigns the class; thresholds only set presentation confidence.** | Nothing guaranteed the ordering, and both demo #3 and #4 depended on it. Also makes the analysis→build link mechanical. |
| **D2** | LLM-enriched descriptions, or hand-write 75? | **Hand-write 75.** | Enrichment could collapse F4 into F1 and make the central finding an artifact of generated text. |
| **D3** | Supabase + Vercel, or static bundle? | ~~Static bundle~~ → **REVERSED 2026-08-06 by the owner: Supabase + Vue3, DB–BE–FE.** See §6. | Originally decided the other way on budget — 3–5 h vs a 15–20 h build, on a graded axis where more hours is not better. The owner's call is that this is a software product, not a demo bundle. The tension is stated in §6 rather than hidden; log the real hours. |
| **D4** | Seed the demand table from `search_log.csv`? | **Yes.** | It was unwired; a fresh demo would have shown "1 search". Bug fix, not a choice. |
| **D5** | Keep `masaż`-in-London, or demo the 1–2 result cliff? | **Swap for the cliff.** | The headline finding had no demo slot; the London case was fabricated and duplicated #1. |
| **D6** | Write the F1–F6 × behaviour coverage table? | **Yes — §4, and shipped in the prototype.** | The brief's hard requirement is completeness including the unfixable. F6 is cut *and stated as cut*. |

**Kept exactly as the draft had it:** the one-sentence thesis; the staff panel as the spine; both
CUT decisions and their reasons; the abstention framing ("knowing when to return nothing is the
product requirement, not an edge case"); the nth-order observation that loosening matching makes
the invisible failure worse.
