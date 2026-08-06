# Part B — build spec
### Groupon case study R29944 · discovery prototype

> **Status: draft, under review.** This is the spec as originally written.
> See `SPEC_REVIEW.md` in this folder for the assessment against
> `PLAN.md` / `FINDINGS.md` and the open decisions. Do not build from this
> file until those decisions are resolved.

**Read `FINDINGS.md` first.** Every behaviour below exists because of a
specific verified finding. If a feature can't be traced back to one, it
isn't in scope.

**The brief's actual test:** the prototype must handle every query type
found in Part A *including the unfixable ones*. Their words: what it does
when it has no good answer tells them as much as what it does when it
succeeds. They explicitly do not grade code quality, visual design, or
whether you wrote the code.

**The one-sentence thesis the build has to prove:**
this is not a search-quality problem, it is a marketplace liquidity
problem that search is merely measuring. The prototype is the instrument
that makes that visible.

---

## 1. Scope — locked

| Priority | Component | Why it's here |
|---|---|---|
| **MUST** | Three failure tiers behave visibly differently | This *is* the finding. Without it the demo is a search bar. |
| **MUST** | Staff panel ("show your working") | Highest-value component for this audience. Answers "show your working" literally. |
| **HIGH** | Demand-capture loop + simulated acquisition brief | Maps to Groupon's named international growth driver: supply expansion. |
| **NICE** | Natural-language query input | Demonstrates the AI-native bar. Rides on the embedding already required. |
| **CUT** | Returning-customer recommendations | No user IDs, no sessions, no purchase history in the dataset. Building it means fabricating evidence — the exact failure they are testing for. |
| **CUT** | Real autonomous vendor-outreach agent | Simulate it. The idea scores; the plumbing does not. |

**Personalization compromise (only if you want it):** two personas that
change *nothing except empty-state copy* — experienced user gets
"notify me", newcomer gets labelled adjacency. Flag it in Part C as a
designed illustration, not a data-supported finding.

---

## 2. The three tiers — required behaviour

The whole grade sits here. Each tier must produce a *visibly different*
screen.

### Tier 1 — Silent mismatch (the invisible failure)
**Finding:** paintball, crossfit, sushi, bowling have **zero** deals in
the catalogue, yet return a median 7–9 results and convert comparably to
in-catalogue queries. Users get a full page that doesn't answer them.

**Behaviour:** below a similarity floor, the system must stop presenting
results as *the answer*. Header changes from "Results for X" to
"We don't have X — you might also like". Same deals, honest frame.

> This is the nth-order point: the obvious fix (loosen matching to cut
> zero-results) makes this tier *worse*. Dashboard goes green, trust goes
> down. Demo this explicitly.

### Tier 2 — Supply void (64.2% of zero-result searches)
**Finding:** 185 market+query pairs return zero *every time* — 1,691 lost
searches, almost all adrenaline/aerial (skydiving, rafting, helicopter,
balloon, supercar). The catalogue holds 4 L1 / 5 L2 categories and
`activities` stocks only city tours, escape rooms, karting. Adrenaline is
47.6% of all zero-result searches. **Search cannot fix this.**

**Behaviour — five things, in value order:**
1. **Name the gap honestly.** "No skydiving in Berlin yet."
2. **Capture intent.** Notify-me writes market + city + concept to the
   demand table. One event serves the user *and* merchant acquisition.
3. **Offer adjacency, clearly labelled.** "Closest thrill we do stock:
   karting." The label is what separates this from Tier 1. Deliberate
   friction where the stakes demand engagement.
4. **Widen geography before concept.** Nearest city with real inventory,
   distance stated. *Not possible in this dataset — no aerial anywhere —
   but structurally it comes first. Say so.*
5. **Show demand back.** "47 people searched this in Berlin last month."

### Tier 3 — Intermittent (35.8% of zero-result searches)
**Finding:** 179 pairs return zero sometimes (942 lost searches), rates
12–25%. Median city-to-city spread within a pair = 0.199 (ES crossfit
runs 0% in one city, 43.8% in another). City-level thinness is real but
doesn't explain all of it; residual points at a ranking threshold —
CANNOT VERIFY without the ranker.

**Behaviour:** cross-lingual match resolves it. `masaż tajski`,
`thai massage`, `massage thai` must all hit the same deals. **Treat 1–2
results as a near-empty state, not a results page** — they convert at
1.7%, i.e. like zero.

---

## 3. Architecture

### Index time — the highest-leverage decision
**Do not embed the deal title.** 568 deals share only 75 unique titles,
and they're generic ("Sesja Wellness", "Wellness-Massage Paket").
Embedding those gets you nothing.

Instead **synthesize a deal document** per listing — title + category_l1 +
category_l2 + city + market + a short LLM-enriched service description —
then embed *that*. One offline pass, cached to file, loaded into the DB.

### Query time
- Multilingual sentence embedding of the raw query. **No translation
  layer** — translation is brittle on slang and typos and adds a failure
  point. A multilingual model puts `masaż` and `massage` in nearly the
  same coordinate. Language stops mattering.
- Cosine similarity against the market's inventory.
- *(Production only, state in Part C, don't build:)* BM25 lexical +
  dense vectors fused via reciprocal rank fusion, cross-encoder re-rank
  of top 50.

### The abstention threshold — the part that actually matters
A vector search **always** returns k neighbours. Cosine is never zero. A
naive implementation therefore **eliminates zero-result searches and
maximises silent mismatch** — the metric looks perfect and the product
gets worse.

So:

```
max_similarity >= HIGH    → confident results ("Results for X")
LOW <= max_sim < HIGH     → labelled adjacency ("We don't have X, but…")
max_similarity <  LOW     → honest empty state + intent capture
```

Calibrate HIGH/LOW by hand against known cases (skydiving must fall below
LOW; masaż tajski must clear HIGH). **State in Part C that these are
hand-calibrated on 568 deals and would need proper calibration against
labelled relevance judgements in production.**

**Knowing when to return nothing is the product requirement, not an edge
case.** Every abstention writes a row to the demand table.

---

## 4. The demand loop

```
abstention event → demand table (market, city, concept, query, count, date)
                 → aggregate by market × city × concept
                 → mocked acquisition brief
```

The brief output: "Berlin · skydiving · 47 searches · 0 deals · est.
lost purchases at 11.5% s2p ≈ 5/month · suggested vendor outreach list."

**Simulate the agent.** A function that reads the table and renders the
brief. Do not build outreach. The demand table *is* the merchant
acquisition feed — that's the differentiating claim, and it sits exactly
where Groupon's two stated priorities intersect (discovery + supply
expansion).

Label the lost-purchase figure an **upper bound**, never a forecast.
Recovered searches convert worse than organic ones.

---

## 5. Staff panel — the spine of the demo

A persistent "Groupon staff view" button. Opens a side panel showing, for
the query just run:

- Raw query, detected language, market/city context
- The embedding match: top 5 deals with cosine scores
- Which threshold band fired, and why
- Which tier this query belongs to (1 / 2 / 3) and the finding behind it
- Whether a demand-table row was written
- **What the system does not know** — e.g. "the log records a result
  count only, no query→deal mapping, so substitution is inferred"

This is the component that converts a prototype into an argument. Build
the demo so the panel is worth opening on every single query.

---

## 6. Stack

**Supabase + Vercel.** Hosted, shareable, one URL to send.

- **Supabase** — Postgres + pgvector. Catalog, embeddings, and demand
  table in one system.
- **Vercel** — front end, deploys from Git push, public link.
- Front end: whatever is fastest for you (Vue 3 / React). Not graded.

**Security/perf:** precompute embeddings offline and load once. Never put
model calls or keys in the browser. The front end only reads. This keeps
the live demo instant — no model latency while a hiring manager clicks.

**The Part C line:** at 568 deals, pgvector inside Postgres isn't just
sufficient, it's *correct* — the catalog is already relational and a
second specialist system would be operational overhead with no benefit at
this scale. Named restraint reads as senior judgment. Say you'd revisit
at Groupon's real scale.

---

## 7. Demo script — the five queries to walk them through

| # | Query | Market | Expected behaviour | Point made |
|---|---|---|---|---|
| 1 | `masaż tajski` | PL | Confident results | Cross-lingual matching works |
| 2 | `masaż` | GB / London | Confident results, London deals | Language ≠ market. *Designed illustration — flag it, this case isn't in the data.* |
| 3 | `paintball` | DE | **Labelled adjacency**, not a full page | Tier 1: the invisible failure, made visible |
| 4 | `fallschirmspringen` | DE | Honest empty state + notify-me + demand row | Tier 2: search can't fix supply |
| 5 | Staff view on #4 → acquisition brief | — | Demand table → vendor brief | The loop closes on the supply side |

Optional 6th: natural-language input — "I'm in London four days with my
family, what can we do?" — to show the enriched query path.

---

## 8. Honesty register — carry these into Part C

State every one of these out loud. Honesty about limits is graded.

- **No query→deal mapping in the log** — only a result count. Tier 1
  substitution is INFERRED from category structure. Cannot distinguish
  happy substitution from a data generator ignoring relevance.
- **No exactly-3-result searches anywhere.** Ranking cut-off or
  generation artifact — cannot tell from this file.
- **No session IDs, no order values.** No repeat-search, abandonment, or
  revenue analysis possible.
- **Data is clean enough to be synthetic.** Say so, and name the four
  things to instrument in week one: query→results mapping, null-result
  events carrying the raw query, session IDs, ranker relevance scores.
- **Thresholds are hand-calibrated**, not learned.
- **Polish-in-London is a designed scenario**, not a measured one.
- **Recovery estimates are upper bounds.**

---

## 9. Fix before quoting anything

`validate.py` Layer 3 has a **known wrong verdict**: the hand-built
concept map routes adrenaline queries to the `activities` L2 category, so
the decisive table prints "MATCHER FAILURE" for skydiving and rafting. It
is a **supply void** — `activities` exists but stocks none of the
requested inventory. *A category existing ≠ a category stocking the
thing.*

Also: the `unmapped` bucket is still 3,806 searches / 883 zeros. Extend
the map — `paracaidismo`, `paseo en globo`, `vol en montgolfière`,
`lot balonem`, `skoki spadochronowe`, `lot helikopterem` are all
adrenaline sitting in unmapped. Adding them raises the adrenaline share.

**Use this as the worked example in the required "what the AI tools got
wrong" log.** It's a better answer than anything invented after the fact:
the tool produced a confident, plausible, wrong verdict, and the concept
map that produced it is exactly why the production design replaces
keyword mapping with embeddings.

---

## 10. Build order

1. Seed the catalog from `deals.csv` into Supabase. Cheap. It's the
   stage, not the play.
2. Offline script: synthesize deal documents → embed → load.
3. Query path: embed → cosine → threshold bands. **Get the three bands
   right before touching the UI.**
4. Three tier screens.
5. Demand table + notify-me writes.
6. Staff panel.
7. Acquisition brief view.
8. Deploy, test the five demo queries end to end.
9. *Then* make it look like Groupon.

Log hours as you go — per-hour productivity is assessed, and the log is a
required deliverable alongside AI tools used and what they got wrong.
