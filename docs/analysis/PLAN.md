---
created: 2026-08-06
updated: 2026-08-06
note: Reduced to derivation only — corrected the live helicopter count (300+ → 11 single-token), the F3/F5 grid cells (causes withdrawn, populations kept) and three stale statements; moved this file's three in-place retractions to FINDINGS.md §9; deleted the two tombstones, the traps list and every paragraph restating a number owned elsewhere.
---

# Groupon R29944 — decomposition and reasoning

Written 2026-08-05; trimmed 2026-08-06 to what is unique to it. Inputs: the case-study brief PDF,
`docs/brief/search_log.csv`, `docs/brief/deals.csv`, the verified Part A findings in
`FINDINGS.md`, and a live reconnaissance pass over groupon.co.uk / .de / .pl.

**This file owns derivation only — not status, not verified numbers, not retractions.** The queue
is in `INDEX.md`; tagged numbers are in `FINDINGS.md`, and every withdrawn claim is in its §9
Corrections register. Unique here: the brief's claims with a testability verdict (§1), what the
data does *not* contain (§2), the live reconnaissance with the exact counts and controls behind it
(§4), and the supply × system-response grid that **derives** F1–F6 (§5).

**F1–F6 exists in three places, not interchangeably:** §5 below *derives* the classes from the
grid, `001-part-b/SPEC.md` §3/§4 is the *behaviour contract*, `FINDINGS.md` §5d carries the
*populations*. Section numbers are deliberately non-contiguous — §3, §6 and §7 were removed and the
rest kept their numbers so existing cross-references still resolve.

---

## 1. What they are claiming

The brief opens with a business framing. Being explicit about which parts are checkable is itself
graded.

| Their claim | Testable with the supplied data? |
|---|---|
| International ≈ ⅓ of orders but < ¼ of revenue | **No.** No order or revenue data. |
| AOV outside the US ≈ 60% of US levels | **No.** No US baseline; `purchased` is a flag with no link to which deal was bought, so `price_usd` cannot be joined to a purchase. |
| "Not finding the right thing often enough" | **Partially.** Dead ends are measurable precisely; "the right thing" is not — no relevance label, no query→deal mapping. **That gap is the whole exercise.** |
| Built for the US: dense supply, English queries | **Partially — and it was the most valuable untested claim.** Tested and confirmed: `FINDINGS.md` §5b, 42.3pp. |
| Thinner inventory internationally | **Within-dataset only.** No US baseline to compare against. |
| "Synthetic but modelled on real market weights" | **Partially.** Volume runs GB 2,587 > ES 1,997 > FR 1,772 > DE 1,724 > PL 917. DE placing fourth is surprising for a European footprint — a question about the generator, not a finding. |

Two framing moves change what a good answer looks like: **"we are deliberately not telling you what
to look for"** makes the obvious metric (zero-result rate) a trap, the first thing that looks like a
finding; and **"handle every kind of query, including the ones you cannot fix"** says in advance
that some demand is unservable and the honest empty state is a graded deliverable, not an error path.

## 2. What is conspicuously missing

Dataset shape is in `FINDINGS.md` §0 and §8. **Missing, and each absence shapes what can be
concluded:**

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

## 4. Live reconnaissance — what real Groupon actually does

Done 2026-08-05/06 against the production sites. **Important caveat: the live catalogue is not the
synthetic dataset.** Live GB stocks **11** helicopter deals (single-token `helicopter`, division
`london`) where the dataset says GB `helicopter tour` is 100% zero — thin in both, empty in only
one. So this pass validates *mechanisms and UX*, not supply numbers; used that way it converts the
dataset's most important INFERRED claim into something observed in the wild. *(An earlier draft of
this caveat read "300+ helicopter tours" — a coarse UI bucket or multi-word count, the exact
artifact class the method below exists to catch. `FINDINGS.md` §9 row 9.)*

**How the query is built.** `/search?query=<raw>` on `.co.uk`, `.de` and `.pl` alike (`/szukaj`
404s on PL — routes are not localised), resolving through `POST /mobilenextapi/graphql`. The German
site carries a "wie Suchergebnisse ermittelt werden" disclosure link — **the affordance for honesty
already exists**.

**Method — exact counts, reproducible.** The term travels as
`filters: [{key:"query", subKey:null, value:{static:"<term>"}}]` inside `BrowseDealFeed`, location
as a `division` string, persisted-query hash `b035b25d…f429`; the call returns
`pagination.totalCount`, an **exact integer**. Everything the UI shows ("80+", "400+", "40+ ofert")
is coarse bucketing on top of it, and those buckets produced **three** of the withdrawn claims in
`FINDINGS.md` §9 (rows 5, 8, 9). All counts below are exact with `division` pinned. The harness is
committed as **`docs/analysis/live_probe.js`** and ships as part of Part A — the brief says "we will
run it or check it", and a script that re-derives the counts is the only way live evidence is
checkable rather than asserted.

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

Standalone controls, same division: `xqzjw` **0**, `dinosaur` **13**, `unicorn` **8**. `xqzjw`
returning 0 is the clean control the rest of the argument needs: it matches nothing, and adding it
changes the count by nothing — 458→458, 56→56, 248→248, 7→7, in two markets on five category heads.

**UPGRADED 2026-08-06 — count equality → exhaustive set equality.** 458 = 458 is equally consistent
with "the same 458 deals" and "a different 458 deals", so the inference was never closed. It is now:
`massage` and `xqzjw massage` were paged to exhaustion via `feedToken` (5 pages, `limit` 100,
division `london`), each yielding **460 unique deal ids, Jaccard 1.0000 — zero ids in one and not
the other**. Two by-products:

- **`totalCount` does not saturate or estimate** — collected ids exactly equalled it (460 = 460),
  so comparisons in the 400s are valid.
- **The inert token is inert on *membership*, not on *ranking*.** Two identical `massage` calls
  return the same 99 ids in the **same order**; `massage` vs `xqzjw massage` returns the same ids in
  a **different order**. `xqzjw` reaches the scorer and perturbs ranking but cannot add, remove or
  filter a single document. **That is the version of F1 to use**, not "the word is ignored" — and
  since `001-part-b/SPEC.md` §3 puts `458 = 458` on screen, the on-screen copy should say the
  upgrade is earned by the id set, not by the count.

*Count drift: `massage`/`london` read 458 twice and 460 an hour later the same day. Pin the date on
every figure; do not read a ±2 difference as an effect.*

**Three API constraints found the same day, each of which silently corrupts a reasonable-looking
probe** — ignored `offset`, silently-falling-back invalid `division`, and two unread facets
(`locations`, `distance`) that measure geographic spread for free. Full detail and the exact
counts: `003-live-validation/QUERIES.md` §0; the two that invalidate prior probes are `INDEX.md`
known issues **#9** and **#10**.

**Not a clean story, and not forced into one.** The multi-term result set is neither a union nor an
intersection of the single-term sets:

| | baseline | + `dinosaur` (13) | plain union would be | actual |
|---|---|---|---|---|
| `massage` | 458 | `dinosaur massage` | 471 | **460** |
| `yoga` | 56 | `dinosaur yoga` | 69 | **65** |
| `pizza` | 40 | `dinosaur pizza` | 53 | **45** |
| `diving` (29) + `shark` (10) | — | `shark diving` | 39 | **81** |

`dinosaur` lands consistently *below* the union; `shark diving` lands at **more than double** it, so
it retrieves documents neither word retrieves alone — genuine query expansion, not a set operation.
In PL the direction reverses: `masaz tajski` (95) is *below* `masaz` (248) though `tajski` alone
returns 28.

The defensible summary: **adding a term does not reliably narrow.** GB went up in every pair tested.
**PL is inconsistent, and that is the stronger claim** — it narrows on 4 of 6 two-token pairs
(`kurs tańca` 312 + `tańca` 4 → **4**) but `joga tajski` *widens*, so the behaviour is not uniform
even within one market and "GB expands, PL intersects" is ruled out. Consistent with scored
retrieval over a threshold plus an expansion stage tuned per market — the ranker config is not
observable from outside and is not guessed at here. `shark diving` pulling 81 documents when
neither word reaches that alone is the machinery that turns "we stock no sharks" into "here are 81
confident results", so the expansion stage needs auditing separately from term-constraining.
*Two claims about this finding were withdrawn: `FINDINGS.md` §9 row 3.*

**Finding 2 — thin sets get padded with filler.** `skydiving` in London returns "2 deals": a COSHH
online workplace-safety course, and a real skydive **141.5 miles away in Devon** — then a gift-card
card and "That's All for Now." The 1–2 result cliff, live.

**Finding 3 — the true zero state misattributes blame.** `fallschirmspringen` on groupon.de
(location Zittau) returns **0 Angebote** with *"Keine Angebote verfügbar. Versuchen Sie, einen der
angewendeten Filter zu entfernen"* — telling the user to remove filters when none are applied. A
"similar offers" carousel sits below, but there is no intent capture, no radius widening, no
notify-me. *(That message is all this observation supports; a radius-inconsistency reading of the
same session was withdrawn — `FINDINGS.md` §9 row 4.)*

**Finding 4 — diacritics cost little on one word, roughly half the result set on two.** Exact
counts, division pinned to `warszawa`:

| Correct Polish | | ASCII, as typed | | Loss |
|---|---|---|---|---|
| `masaż` | 272 | `masaz` | 248 | −8.8% |
| `masaż tajski` | 162 | `masaz tajski` | 95 | **−41%** |
| `masaż relaksacyjny` | 215 | `masaz relaksacyjny` | 112 | **−48%** |

So the matcher is largely diacritic-tolerant on a *single* token — the naive "Polish users are
locked out" story is wrong — and the penalty lands on multi-word queries. Sharper and more
actionable, because it says *where* to fix it. *(A "4× recall" reading off the UI buckets was
withdrawn: `FINDINGS.md` §9 row 5. The live follow-up narrows it further to the `masaż` token
family: §5e.)*

**Finding 5 — cross-language works for cognates.** English `thai massage` on groupon.de returns
20+ German Thai-massage merchants. The matcher is not monolingual; it is *lexical*, and it succeeds
exactly where the words happen to look alike.

**Finding 6 — autocomplete returns a server error for every query.** `SuggestedSearchQueries`
responds `INTERNAL_SERVER_ERROR`, *"Cannot read properties of undefined (reading 'logError')"*,
`data: null` — 100% of queries tried. The layer where spell correction, synonym expansion and query
understanding would live is returning nothing, which is consistent with everything above: no
query-understanding stage drops terms because that stage is dark. **Re-checked and it holds** — 5/5
errors on `groupon.co.uk` 2026-08-05, then 3/4 on `groupon.pl` 2026-08-06, so **cross-host and
cross-day**, not a single-session artifact (`FINDINGS.md` §5e). Safe for Part C.

**Synthesis:** one root cause — retrieval scores the query as a bag of *optional* terms against
short generic titles. Dense US supply hides that; thin international supply exposes it. A claim
about *observable effect* only: ranker internals are not visible from outside.

## 5. The decomposition

"Search is broken" is not one problem. Model each search as a cell in a grid of
**what supply actually exists** × **how the system responded**:

| | R1 returns it, ranked top | R2 returns it, buried | R3 returns nothing | R4 returns something else, silently |
|---|---|---|---|---|
| **S1** exists in this city | ok | ranking | **F5** *(residual — cause not established)* | **F1 / F6** |
| **S2** exists in market, other city | ok-ish | ranking | **F3** *(population only — see note)* | **F1** |
| **S3** exists in another market only | — | — | F3′ | **F1** |
| **S4** does not exist on Groupon | — | — | **F4** | **F1** |

**The zero-result metric only ever sees column R3.** Column R4 — a full page of confident, wrong
results — is invisible to every dashboard Groupon currently has, and Finding 1 shows it happening
in production right now.

**Two cells are placements the evidence no longer supports, marked rather than redrawn.** S1×R3 =
F5 and S2×R3 = F3 each asserted a *cause* — a ranking cut-off, and inventory in another city. Both
causes were withdrawn (`FINDINGS.md` §9 rows 7 and 10); both **populations survive**. Read those
cells as where the class was *hypothesised* to sit, not where its members are. The grid's
load-bearing work — R3 and R4 are different failures, only R3 instrumented — does not depend on
either.

That yields six failure classes, each with a different owner, fix and metric:

| # | Class | Evidence | Owner | Fix | Prototype must |
|---|---|---|---|---|---|
| **F1** | Silent substitution — query terms are optional, so nothing you type constrains results | Live, exact: `xqzjw massage` = `massage` = 458 (GB); `xqzjw masaz` = `masaz` = 248 (PL). Data: paintball, crossfit, sushi, bowling stocked nowhere yet returning full pages | Search relevance | Require/score the discriminating term + **disclose which terms were honoured** | Name what it could not match, before showing alternatives |
| **F2** | Lexical & morphological miss | Live, exact: `masaż tajski` 162 → `masaz tajski` 95 (−41%); single-token loss only −8.8%. Data: local-language intermittency | Search / i18n | Diacritic folding **on multi-token queries**, synonyms, multilingual embeddings | Match `masaz`≡`masaż`; show it did |
| **F3** | **Uneven across cities** — a population, cause not established | Data: assigned on city-to-city variance in dead rate (`city_spread >= 0.25`), which is a *symptom*. Median city spread 0.199; corr(deals, zero-rate) = −0.379, n=20. **Not** a location claim: only 6 of its 321 dead ends have the answering deal in another city | Ranking / UX | Unknown — diagnose before fixing. Radius widening is only correct for the 6 | **Not** "just not in your city" — that copy was false for 315 of 321 rows. Say the result is uneven and do not name a cause |
| **F4** | Category void | Data: 64.2% of zeros; adrenaline = 47.6% of all zeros | **Merchant acquisition, not search** | Honest empty state + demand capture → acquisition feed | Say we don't have it, capture the intent, log the demand |
| **F5** | **Unexplained residual** — stocked, failing, and not F2 or F3 | Assigned by `classify.py` as a residual, not diagnosed. Its "ranking cutoff" basis (no query returns exactly 3) was a **generation artifact** — live Groupon returns 3 routinely. Same-city intermittency is real but unattributed | Unowned until diagnosed | Instrument first: this is the ask for query→results mapping and a relevance label | Degrade gracefully rather than snapping to zero — **without claiming to know why** |
| **F6** | Intent-type confusion | Live: `shark` → 10 results, all shark blankets/socks/water pistols (Goods, not experiences) | Intent classification | Separate goods from local experiences | Ask or split, don't blend |

This grid is the deliverable of Part A and the specification for Part B. It is
also the answer to the brief's second grading criterion — the prototype reflects
the analysis because **each class maps to a visibly different behaviour**.
