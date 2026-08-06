# Groupon R29944 — decomposition and reasoning

Written 2026-08-05; trimmed 2026-08-06 to what is unique to it. Inputs: the case-study brief PDF,
`docs/brief/search_log.csv`, `docs/brief/deals.csv`, the verified Part A findings in
`FINDINGS.md`, and a live reconnaissance pass over groupon.co.uk / .de / .pl.

**This file holds reasoning, not status and not numbers.** Status and the work queue are in
`INDEX.md`; verified numbers are in `FINDINGS.md`. What is unique here: the brief's claims with a
testability verdict (§1), what the data does and does not contain (§2), the live reconnaissance
including three claims retracted in place (§4), the supply × system-response grid that yields the
**F1–F6 taxonomy** (§5 — the only copy), and the traps (§7).

---

## 1. What they are claiming

The brief opens with a business framing. Not all of it is checkable with what
they gave us, and being explicit about which is which is one of the things they
say they are grading.

| Their claim | Can we test it with the supplied data? |
|---|---|
| International markets ≈ ⅓ of orders but < ¼ of revenue | **No.** No order or revenue data at all. |
| AOV outside the US ≈ 60% of US levels | **No.** No US baseline, and `purchased` is a flag with no link to which deal was bought. `price_usd` exists but cannot be joined to a purchase. |
| "Customers are finding us and buying. They are just not finding the right thing often enough." | **Partially.** We can measure dead ends precisely. We cannot measure "the right thing" — there is no relevance label and no query→deal mapping. This gap is the whole exercise. |
| Search/browse/homepage built for the US: dense supply, English queries | **Partially, and this is the most valuable untested claim.** See task 1.3. |
| Thinner inventory in international markets | **Within-dataset only.** 568 deals, 15 unique titles per market, 5 L2 categories. No US baseline to compare against. |
| "Synthetic but modelled on real patterns and real market weights" | **Partially checkable, and worth checking.** Search volume runs GB 2,587 > ES 1,997 > FR 1,772 > DE 1,724 > PL 917. DE placing fourth is surprising for a European Groupon footprint. Flag as a question about the generator, not as a finding. |

Two framing moves in the brief are worth noticing because they change what a
good answer looks like:

- **"We are deliberately not telling you what to look for."** The obvious metric
  (zero-result rate) is a trap — it is the first thing that looks like a finding.
- **"Your prototype has to handle every kind of query you found in Part A,
  including the ones you cannot fix."** They are telling you in advance that some
  of the demand is unservable, and that the honest empty state is a graded
  deliverable, not an error path.

## 2. What they gave us, and what is conspicuously missing

**Given:** `search_log.csv` (8,997 searches, June 2026, 613 unique queries,
5 markets × 4 cities) and `deals.csv` (568 live deals, 75 unique titles,
4 L1 / 5 L2 categories).

**Missing, and each absence shapes what can be concluded:**

- **Query → deal mapping.** `results_shown` is a bare count. We can never observe
  *what* was returned, only *how many*. This single omission is what makes the
  most important failure mode invisible.
- **Relevance scores / ranker output.** So "intermittent" queries cannot be
  attributed to a threshold vs. thin supply.
- **Session IDs, timestamps, reformulations.** No way to see a user retrying,
  narrowing, or giving up — the strongest behavioural signal of a bad result set.
- **Impressions and position.** No way to distinguish "not returned" from
  "returned and buried".

The brief says to state what you would ask for in production. That list above
*is* the ask, and it should appear in Part C.

## 3. What is already established (Part A, verified)

**Moved.** Every verified number now lives in one place: `FINDINGS.md`, where each statement
carries its VERIFIED / INFERRED / CANNOT VERIFY tag. This section held a fourth copy of the
headline figures and was the one nobody re-ran.

## 4. Live reconnaissance — what real Groupon actually does

Done today against the production sites. **Important caveat: the live catalogue is
not the synthetic dataset.** Live GB stocks 300+ helicopter tours; the dataset says
GB helicopter tour is 100% zero. So this pass validates *mechanisms and UX*, not
supply numbers. Used that way, it converts the dataset's most important INFERRED
claim into something observed in the wild.

**How the query is built.** URL contract is `/search?query=<raw>` on `.co.uk`,
`.de` and `.pl` alike (`/szukaj` 404s on PL — the routes are not localised).
Search resolves through `POST /mobilenextapi/graphql`; the front end is a
TanStack-based PWA served off `grouponcdn.com`. Filters are price, rating,
giftable, bookable-online and location, plus sort and a map view. The German site
carries a "wie Suchergebnisse ermittelt werden" ("how search results are
determined") disclosure link — the affordance for honesty already exists.

**Method — exact counts, reproducible.** The search term travels as
`filters: [{key:"query", subKey:null, value:{static:"<term>"}}]` inside
`BrowseDealFeed`, with location as a `division` string (`london`, `warszawa`) and
a persisted-query hash `b035b25d…f429`. Replaying that call returns
`pagination.totalCount` — an **exact integer**. Everything the UI shows ("80+",
"400+", "40+ ofert") is coarse bucketing on top of it, and those buckets are
misleading enough to have produced two wrong claims in an earlier draft of this
file. All counts below are exact, with `division` pinned so location cannot
confound the comparison. The harness is committed as **`docs/analysis/live_probe.js`**
and ships as part of Part A — the brief says "we will run it or check it", and a
script that re-derives the live counts is the only way the live evidence is
checkable rather than asserted.

**Candidate headline for Part C.** The GB/PL divergence below — same platform,
demonstrably different query semantics per market — sits closer to the brief's
actual thesis (a US-built system deployed across five countries) than anything in
the synthetic data. It is currently a caveat inside Finding 1; task 1.7(a)
queues the confirmation work needed to promote it to a finding in its own right.

**Finding 1 — query terms are optional. A word that matches nothing is a no-op,
and the user is never told.**

GB, division `london`:

| Query | totalCount | | Query | totalCount |
|---|---|---|---|---|
| `massage` | 458 | | `diving` | 29 |
| `xqzjw massage` | **458** | | `shark` | 10 |
| `unicorn massage` | 459 | | `shark diving` | **81** |
| `dinosaur massage` | 460 | | `unicorn` | 8 |
| `yoga` | 56 | | `skydiving` | 2 |
| `xqzjw yoga` | **56** | | `paintball` | 12 |
| `dinosaur yoga` | 65 | | `escape room` | 120 |
| `pizza` | 40 | | `dinosaur pizza` | 45 |

PL, division `warszawa`: `masaz` 248 · `xqzjw masaz` **248** · `dinozaur masaz`
**248** · `joga` 7 · `xqzjw joga` **7**.

Standalone controls, same division: `xqzjw` **0**, `dinosaur` **13**, `unicorn`
**8**. `xqzjw` returning 0 is the clean control the rest of the argument needs.

**What is nailed down**, in two markets, on five category heads:

**A zero-match token is exactly inert.** `xqzjw` matches nothing (0 standalone),
and adding it changes the count by nothing: 458→458, 56→56, 248→248, 7→7. Not
"approximately"; identical. The system does not require your words to match, does
not filter on them, and never signals that a word did nothing. **This is F1, and
it is now exact rather than inferred.**

**UPGRADED 2026-08-06 — from count equality to exhaustive set equality.** Everything
above is a *count* comparison, and 458 = 458 is equally consistent with "the same 458
deals" and with "a different 458 deals". The inference was never closed. It is now:
both `massage` and `xqzjw massage` were paged to exhaustion via `feedToken` (5 pages,
`limit` 100, division `london`) and each yielded **460 unique deal ids with Jaccard
1.0000 — zero ids in one and not the other**. Not a sample of the top 99; the whole
result set. `001-part-b/SPEC.md` §3 puts `458 = 458` on screen as the artifact that
moves F1 from CANNOT VERIFY toward observed; **that upgrade is earned by the
exhaustive id-set result, not by the count**, and the on-screen copy should say so.

Two by-products of that run:

- **`totalCount` does not saturate or estimate.** Collected unique ids exactly equalled
  it (460 = 460), so the integer is a real enumerable count and comparisons in the
  400s are valid.
- **The inert token is inert on *membership*, not on *ranking*.** Two identical
  `massage` calls return the same 99 ids in the **same order**; `massage` vs
  `xqzjw massage` returns the same ids in a **different order**. So `xqzjw` does reach
  the scorer and perturbs ranking — it simply cannot add, remove or filter a single
  document. That is a sharper statement of F1 than "the word is ignored", and it is
  the version to use.

*Count drift: `massage`/`london` read 458 twice and 460 an hour later on the same day.
Live counts move by a couple over hours — pin the date on every figure and do not read
a ±2 difference as an effect.*

**Three API constraints found the same day, each of which silently corrupts a
reasonable-looking probe** — full detail in `003-live-validation/QUERIES.md` §0:

- **`offset` is ignored** unless `feedToken` is echoed back with `isFetchMore:true`.
  `offset:400` returns page 1. Any deep-paging probe that walks `offset` is
  measuring the first page over and over.
- **An invalid `division` does not error.** It falls back to a default scope and
  `browseProps.division` echoes back whatever was *sent*, so the echo is not
  confirmation. On `.fr`: `paris` → 444, while `not-a-division` and `zzzzqqq` both
  → 399. This is the `warsaw`/`warszawa` trap, and it is worse than previously
  recorded — there is no error signal at all, only a plausible wrong number.
- **Two facets we were never reading**, free on every call: `facets.locations`
  (per-town counts for the query) and `facets.distance` (a cumulative distance
  histogram — `massage`/`paris` is 19 within 1 km, 198 within 5 km, of 444 total).
  The second one turns Finding 2's "thin sets get padded with filler" into a
  measurable per-query ratio instead of a screenshot.

**What is not a clean story, and I am not going to force one.** The multi-term
result set is neither a union nor an intersection of the single-term sets:

| | baseline | + `dinosaur` (13) | plain union would be | actual |
|---|---|---|---|---|
| `massage` | 458 | `dinosaur massage` | 471 | **460** |
| `yoga` | 56 | `dinosaur yoga` | 69 | **65** |
| `pizza` | 40 | `dinosaur pizza` | 53 | **45** |
| `diving` (29) + `shark` (10) | — | `shark diving` | 39 | **81** |

Adding `dinosaur` lands consistently *below* the union; `shark diving` lands at
**more than double** it. So `shark diving` retrieves documents that neither
`shark` nor `diving` retrieves alone — that is genuine query expansion, not a set
operation. And in PL the direction reverses entirely: `masaz tajski` (95) is
*below* `masaz` (248) even though `tajski` alone returns 28.

The defensible summary: **adding a term does not reliably narrow.** In GB every
pair tested went up; in PL it went down. Consistent with scored retrieval over a
relevance threshold, plus an expansion stage, tuned differently per market — but
the ranker config is not observable from outside and I will not guess at it.

This matters for the platform ask, which is therefore **two** things, not one:
make the discriminating term actually constrain, *and* audit the expansion stage —
because `shark diving` pulling 81 documents when neither word reaches that alone
is precisely the machinery that turns "we stock no sharks" into "here are 81
confident results".

**Corrections to earlier drafts of this file.** I first called this "silent
token-dropping" and wrote that the 80+ for `shark diving` "came entirely from
*diving*" — both wrong; dropping cannot raise a count, and `diving` alone is 29.
I then claimed a real-but-unstocked word "widens the result set" as though it were
a property of the query semantics — also overreach, since `dinosaur` has 13
matches of its own and the arithmetic above does not fit a union either. Kept
visible on purpose: this is the failure mode the brief is probing for.

**Finding 2 — thin sets get padded with filler.** `skydiving` in London returns
"2 deals": a COSHH online workplace-safety course, and a real skydive 141.5 miles
away in Devon — followed by a Groupon gift-card card and "That's All for Now."
This is the 1–2 result cliff, live.

**Finding 3 — the true zero state misattributes blame.** `fallschirmspringen` on
groupon.de (location Zittau) returns **0 Angebote** with the message *"Keine
Angebote verfügbar. Versuchen Sie, einen der angewendeten Filter zu entfernen"* —
telling the user to remove filters when no filters are applied. A "similar offers"
carousel sits below, but there is no intent capture, no radius widening, no
notify-me.

(An earlier draft called it inconsistent that the same session served Thai massage
results 75–79 km away but returned zero for skydiving. That was an inference, not
an observation — a finite maximum radius with no skydiving inside it produces the
same result with no inconsistency at all, and I never checked whether German
skydiving exists near Zittau. Dropped. What survives is what the screenshot shows
plainly: **the message blames filters the user has not applied.**)

**Finding 4 — diacritics cost little on one word and roughly half the result set
on two.** Exact counts, division pinned to `warszawa`:

| Correct Polish | | ASCII, as typed | | Loss |
|---|---|---|---|---|
| `masaż` | 272 | `masaz` | 248 | −8.8% |
| `masaż tajski` | 162 | `masaz tajski` | 95 | **−41%** |
| `masaż relaksacyjny` | 215 | `masaz relaksacyjny` | 112 | **−48%** |

So the matcher is largely diacritic-tolerant on a *single* token — the naive
"Polish users are locked out" story is wrong. The penalty appears on multi-word
queries, where dropping diacritics costs roughly half the inventory. That is a
sharper and more actionable finding than the original, because it says *where* to
fix it.

**This corrects an earlier draft twice over.** I had read the UI labels as "40+"
vs "10+" and inferred "4× recall". The true figures are 162 vs 95 — the buckets
were coarse *and* the two runs had an unpinned location. Both the ratio and the
framing were wrong. Worth keeping visible as a worked example of the brief's
"claims survive us checking them" criterion.

**Finding 5 — cross-language works for cognates.** English `thai massage` on
groupon.de returns 20+ German Thai-massage merchants. So the matcher is not
monolingual; it is *lexical*, and it succeeds exactly where the words happen to
look alike.

**Finding 6 — autocomplete is returning a server error for every query.**
`SuggestedSearchQueries` responds `INTERNAL_SERVER_ERROR`, *"Cannot read
properties of undefined (reading 'logError')"*, with `data: null` — for `massage`,
`mass`, `skydiv`, `pizza` and `shark diving`, i.e. 100% of queries tried. The
layer where spell correction, synonym expansion and query understanding would
normally live is currently returning nothing at all, which is consistent with
everything above: there is no query-understanding stage to drop terms, because
that stage is dark. **Caveat: observed on one day, from one client, in one
session.** It could be a transient regression, or geo/consent-specific. Re-check
before putting it in Part C — but if it holds, "your autocomplete is 500ing in
production" is worth more than most of the analysis.

**Synthesis:** these are one root cause. Retrieval treats the query as a bag of
optional terms scored against short generic titles. Terms that match nothing
contribute nothing; adding terms does not reliably narrow (GB went up in every
pair tested, PL went down); nothing the user types constrains the result set; and
the interface never distinguishes "we
found what you asked for" from "we found things, none of which are what you asked
for". Dense US supply hides this — with enough inventory, a loosely-matched set
usually contains something acceptable anyway. Thin international supply exposes
it. This is a claim about *observable effect*; the ranker internals are not
visible from outside, and the PL narrowing case shows they are not uniform.

## 5. The decomposition

"Search is broken" is not one problem. Model each search as a cell in a grid of
**what supply actually exists** × **how the system responded**:

| | R1 returns it, ranked top | R2 returns it, buried | R3 returns nothing | R4 returns something else, silently |
|---|---|---|---|---|
| **S1** exists in this city | ok | ranking | **F5** | **F1 / F6** |
| **S2** exists in market, other city | ok-ish | ranking | **F3** | **F1** |
| **S3** exists in another market only | — | — | F3′ | **F1** |
| **S4** does not exist on Groupon | — | — | **F4** | **F1** |

**The zero-result metric only ever sees column R3.** Column R4 — a full page of
confident, wrong results — is invisible to every dashboard Groupon currently has,
and Finding 1 shows it is happening in production right now.

That yields six failure classes, each with a different owner, fix and metric:

| # | Class | Evidence | Owner | Fix | Prototype must |
|---|---|---|---|---|---|
| **F1** | Silent substitution — query terms are optional, so nothing you type constrains results | Live, exact: `xqzjw massage` = `massage` = 458 (GB); `xqzjw masaz` = `masaz` = 248 (PL). Data: paintball, crossfit, sushi, bowling stocked nowhere yet returning full pages | Search relevance | Require/score the discriminating term + **disclose which terms were honoured** | Name what it could not match, before showing alternatives |
| **F2** | Lexical & morphological miss | Live, exact: `masaż tajski` 162 → `masaz tajski` 95 (−41%); single-token loss only −8.8%. Data: local-language intermittency | Search / i18n | Diacritic folding **on multi-token queries**, synonyms, multilingual embeddings | Match `masaz`≡`masaż`; show it did |
| **F3** | Geographic thinness | Data: median city spread 0.199; corr(deals, zero-rate) = −0.379, n=20 | Ranking / UX | Explicit radius widening with distance framing | Offer "20 in Kraków, 90 min away" as a *choice* |
| **F4** | Category void | Data: 64.2% of zeros; adrenaline = 47.6% of all zeros | **Merchant acquisition, not search** | Honest empty state + demand capture → acquisition feed | Say we don't have it, capture the intent, log the demand |
| **F5** | Ranking cutoff | Data: no query ever returns exactly 3; same-city intermittency | Ranking | Investigate the threshold | Degrade gracefully rather than snapping to zero |
| **F6** | Intent-type confusion | Live: `shark` → 10 results, all shark blankets/socks/water pistols (Goods, not experiences) | Intent classification | Separate goods from local experiences | Ask or split, don't blend |

This grid is the deliverable of Part A and the specification for Part B. It is
also the answer to the brief's second grading criterion — the prototype reflects
the analysis because **each class maps to a visibly different behaviour**.

## 6. Next steps

**Moved to `INDEX.md`.** The phase list lived here *and* in INDEX's Pending queue; INDEX was
being updated and this was not, so it kept claiming finished work was still ahead. INDEX owns
the queue and its statuses. This file owns the reasoning behind the queue.

## 7. Traps to avoid

- Leading with **spell-correction**. It is 1.9–7.5% of zeros depending on
  definition, and most typos already resolve.
- Shipping a **pretty semantic search bar** and calling it done (Option A).
- Presenting the **299-purchase upper bound** as a forecast (recomputed 2026-08-06; it read 303
  off a stale 11.5% s2p).
- Building a **per-market narrative** when the confidence intervals overlap.
- Stating "paintball returns escape rooms" as **observed** — it is inferred from
  the category structure. The live site supports the mechanism; the dataset does
  not record it.
- Conflating **live groupon.com behaviour with the synthetic dataset**. The live
  pass proves how the matcher fails, not what the supplied catalogue contains.
