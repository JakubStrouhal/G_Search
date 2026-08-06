# Part B — build spec

Groupon case study R29944 · discovery prototype. **Approved to build, 2026-08-06.**

Supersedes `BUILD_SPEC.md` (draft) and `SPEC_REVIEW.md` (its review), both in `archive/`. The
review's six open decisions **D1–D6 are resolved here** — see §11. Build from this file only.

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
fitness, beauty, dining and massage there is **no principled reason paintball scores above `LOW`
and skydiving below it** — karting may sit closer to skydiving's thrill vector. The demo script
depended on an ordering nothing guaranteed.

**Resolution — the contract already exists.** `docs/analysis/outputs/query_classes.csv` is 751
market+query rows with `failure_class`, `concept`, `searches`, `zeros`, `deads`, `city_spread`,
`coverage`, `deals_stocking`, `is_english`. So:

- **`query_classes.csv` assigns the class.** Deterministic, traceable to Part A, immune to the
  ordering problem. This is a `fetch()`, not new work.
- **Thresholds set presentation confidence *within* the class.** Still the interesting product
  mechanic, still worth demoing, no longer load-bearing for the demo script.
- **The staff panel shows both**, so a grader sees agreement — or disagreement, which is honest and
  more interesting than either alone.

This directly answers the grading criterion *"whether the prototype reflects the analysis rather
than being a nice search UI bolted on beside it"*: the connection becomes mechanical rather than
asserted.

**Unknown queries** (not in the CSV) fall back to the threshold path. Say so in the staff panel.

---

## 3. Required behaviour per class

### F1 — Silent substitution (259 pairs, 1,326 searches) · the invisible failure

**Finding.** paintball, crossfit, sushi, bowling have **zero** deals in the catalogue yet return a
median 7–9 results. GB paintball: 102 searches, 6.9% zero-rate — statistically indistinguishable
from a query the catalogue stocks. Live production proof of the mechanism, exact and replayed:
`xqzjw massage` = `massage` = **458 results**; `xqzjw masaz` = `masaz` = **248**; `xqzjw` alone
returns 0. A zero-match token is *exactly inert* — nothing you type constrains the results.

**Behaviour.** Below the similarity floor the system stops presenting results as *the answer*.
Header changes from "Results for X" to **"We don't have X — you might also like"**. Same deals,
honest frame. **Name the token that could not be matched** before showing alternatives.

Put `458 = 458` on the screen and in the staff panel. It moves the riskiest claim in the build from
inference (`FINDINGS.md` §3 is tagged CANNOT VERIFY) to observation.

> **The nth-order point — demo this explicitly.** The obvious fix, loosening matching to cut
> zero-results, makes this tier *worse*. The dashboard goes green while trust goes down.

### F4 — Supply void (178 pairs, 1,689 searches) · search cannot fix this

> **Two numbers exist for this population and both are right. Do not average them, and do not let
> the prototype and Part C quote different ones.**
> - `FINDINGS.md` says **185 pairs / 1,691 searches / 64.2% of all zeros** — `validate.py`'s rule,
>   `zero_rate == 1.0`, regardless of whether the catalogue stocks the concept.
> - `query_classes.csv` says **178 pairs / 1,689 searches** — `classify.py`'s rule,
>   `coverage == 'absent' AND zero_rate >= 0.5`.
>
> 170 pairs satisfy both. The 21 always-zero pairs that are *not* F4 are almost all **n=1 typos**
> (`skyiving`, `tintee pelo`, `masssage dos`) against concepts the catalogue does stock — correctly
> excluded from a supply-void count. The 8 F4 pairs that are not always-zero are absent concepts
> failing 50–99% of the time. **The classifier's rule is the better one for the prototype**; the
> difference is a definition, not an error. See `INDEX.md` known issue #6.

**The prototype quotes per-cell counts** (GB helicopter tour 100/100/0), which are directly
computed and identical under both rules. Do not put an aggregate pair count in UI copy.

**Finding.** These pairs return zero *every single time*, almost all adrenaline/aerial. GB
helicopter tour 100 searches / 100 zeros / 0 deals stocking it; GB skydiving 91/91/0; DE
fallschirmspringen 64/64/0. `activities` stocks only city tours, escape rooms and karting.

**Behaviour, in value order:**
1. **Name the gap honestly** — "No skydiving in Berlin yet."
2. **Capture intent.** Notify-me writes market + city + concept to the demand table. One event
   serves the user *and* merchant acquisition.
3. **Offer adjacency, clearly labelled** — "Closest thrill we do stock: karting." The label is what
   separates this from F1. Deliberate friction where the stakes demand engagement.
4. **Widen geography before concept** — structurally it comes first. *Not demoable for adrenaline
   (none anywhere), but demoable for real on F3. Say so rather than cutting it.*
5. **Show demand back** — "37 people searched this in Berlin last month." **Real number** (§5).

### F2 — Lexical/morphological miss (65 pairs, 358 searches)

**Finding.** Live and exact: `masaż tajski` 162 → `masaz tajski` 95 (**−41%**), while single-token
diacritic loss costs only −8.8%. The penalty is multi-token. Plus the matched-pair language test:
English phrasing dead-ends at **81.2%** vs **39.0%** for local phrasing — a 42.3pp gap, 47 of 48
pairs, both the supply and rarity confounds killed.

**Behaviour.** `masaż tajski`, `masaz tajski`, `thai massage`, `massage thai` all hit the same
deals. **Show that it did** — display the normalisation that fired.

### F3 — Geographic thinness (15 pairs, 645 searches)

**Finding.** Median city-to-city spread within a pair 0.199; ES crossfit runs 0% in one city and
43.8% in another; corr(deals, zero-rate) = −0.379 across 20 cells (a direction, not an effect).

**Behaviour.** Explicit radius widening with distance stated, offered as a **choice** — "20 in
Kraków, 90 minutes away" — not a silent substitution.

### F5 — Ranking cutoff (73 pairs, 658 searches)

**Finding.** No query anywhere returns exactly 3 results — the distribution runs 0, 1, 2, then
jumps to 4. Cannot be told apart from a generator artifact from this file.

**Behaviour.** Degrade gracefully rather than snapping to zero. **Treat 1–2 results as a near-empty
state, not a results page** — they convert at 1.7% s2p, i.e. like zero.

### F6 — Intent-type confusion · **cut, and stated as cut**

**Finding.** Live only: `shark` returns 10 results, all shark blankets, socks and water pistols —
Goods, not local experiences.

**Cut because** this catalogue contains no Goods, so the class cannot occur in the dataset. It is
in the coverage table (§4) marked cut with this reason. A grader checks for it in ten seconds;
silent absence reads as not having noticed.

### BASELINE (161 pairs, 4,321 searches) · the uncomfortable residual

Queries the catalogue plausibly covers that still dead-end ~40% of the time. Not a named failure
class — it is what is left after the six, and it is the largest bucket by volume. The prototype
does not claim to fix it. **State it in Part C**; a taxonomy that accounts for everything is a
taxonomy that has been fitted.

---

## 4. The coverage table — a required deliverable

The brief's hard requirement is "every query type found in Part A, **including the ones you cannot
fix**." Ship this table in the prototype itself, not just in Part C.

| Part A class | Pairs / searches | Prototype behaviour | Demo query | Fixable by search? |
|---|---|---|---|---|
| **F1** silent substitution | 259 / 1,326 | Name the unmatched token; reframe as labelled adjacency | `paintball` (GB) | Partly — needs term-constraining |
| **F2** lexical/morphological | 65 / 358 | Normalise; show the normalisation | `masaz tajski` (PL) | **Yes** — the genuinely fixable layer |
| **F3** geographic thinness | 15 / 645 | Radius widening as an explicit choice | `crossfit` (FR) | Partly — UX, not relevance |
| **F4** supply void | 178 / 1,689 | Honest empty state + intent capture + acquisition feed | `fallschirmspringen` (DE) | **No** — merchant acquisition |
| **F5** ranking cutoff | 73 / 658 | Treat 1–2 results as near-empty | 1–2 result case (§7 #2) | Unknown — needs the ranker |
| **F6** intent-type confusion | live only | — | — | **Cut:** no Goods in this catalogue |
| BASELINE residual | 161 / 4,321 | No claim made | — | Unexplained — stated, not fixed |

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

**Calibrate against the labelled set Part A already emits, not against two anchor cases.** 178
always-zero pairs plus the never-zero set are a few hundred labelled pairs sitting in
`query_classes.csv`. Sweep HIGH/LOW against them and **report the error rate**. "Thresholds
calibrated against N labelled pairs from Part A, X% disagreement, here are the failures" is
*evidence*; hand-tuning two scalars against two cases is fitting, and Part C would have to confess
it. This sweep doubles as the verification that §2's ordering concern is real.

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

**Demo #2 replaces the draft's `masaż`-in-GB/London scenario**, which was a fabricated case in a
five-query script where honesty is graded, and which only re-made #1's point. The 52.5% headline
had no demo slot at all; now it has the second one.

---

## 8. Staff panel — the spine of the demo

A persistent "Groupon staff view" button. For the query just run, shows:

- Raw query, detected language, market/city context
- The embedding match: top 5 deals with cosine scores, and the matched *document*
- Which threshold band fired, and why
- **Which F-class `query_classes.csv` assigns, and whether the threshold agrees** (§2)
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
- **No search returns exactly 3 results.** Ranking cutoff or generation artifact — cannot tell.
- **No session IDs, no order values.** No repeat-search, abandonment or revenue analysis possible.
- **Data is clean enough to be synthetic.** Say so, and name the four things to instrument in week
  one: query→results mapping, null-result events carrying the raw query, session IDs, ranker
  relevance scores.
- **Thresholds are calibrated against Part A's labelled pairs, not learned**, and the error rate is
  reported rather than hidden.
- **Recovery estimates are upper bounds.** The all-zeros recovery bound is **299 purchases**
  (2,633 zero-result searches × 11.36% s2p), recomputed 2026-08-06.
- **The BASELINE residual is unexplained** — 4,321 searches, ~40% dead, no fix claimed.
- **The two concept maps disagree, and it shows up here.** `classify.py`'s map puts 1,576 searches
  under `adrenaline`, all zeros — 59.9% of all 2,633 zeros. `FINDINGS.md` quotes **47.6%** from
  `validate.py`'s narrower map. **Do not put an adrenaline share in UI copy until they are
  reconciled** (`INDEX.md` known issue #2). Quote per-cell counts, which are directly computed.
- **Two taxonomies over one population.** `FINDINGS.md` splits zeros 64.2% supply void / 35.8%
  intermittent; this spec uses F1–F6, which dissolves "intermittent" into F2 + F3 + F5. These are
  two views of the same searches, not two findings. Part C must say so explicitly, or a grader
  reading both sees a contradiction.
- **The classifier's concept map misfires on typo'd queries.** `paaracaidismo` is mapped to
  `massage`; `skyiving` / `skydiiving` / `shaark diving` to `dining_generic`. Every affected row is
  n=1, so no headline moves — but the staff panel shows the concept, so it will display a visibly
  wrong one on those queries. Either fix the map or exclude `thin_n` rows from the panel.

---

## 10. Build order

1. Supabase project + migrations: `deals`, `deal_documents`, `embeddings` (pgvector),
   `query_classes`, `demand_events`. Seed from `deals.csv` and `query_classes.csv`. The stage, not
   the play.
2. Hand-write the 75 service descriptions. Commit the file.
3. Offline: build documents → embed → load vectors into Postgres.
4. **Sweep HIGH/LOW against Part A's labelled pairs; report the error rate.** Get the three bands
   right — and know how wrong they are — before touching UI.
5. Vue3 class-specific screens (F1, F2, F3, F4, F5).
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
