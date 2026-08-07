---
created: 2026-08-06
updated: 2026-08-06
note: Results of P1-P6 replayed read-only against live groupon.co.uk and groupon.pl on 2026-08-06, with the instrument checks that guard them.
---

# Live validation P1–P6 — results

Run 2026-08-06 against **www.groupon.co.uk** (division `london`) and **www.groupon.pl** (division
`warszawa`). Instrument: `docs/analysis/live_probe.js`, replayed read-only in the page context.
Predictions were pre-registered in `BRIEF.md` before any of this was run.

**Catalogue tag.** Everything on this page describes **live production Groupon**. It says nothing
about the supplied CSVs, which are a different catalogue. Where a live result changes what the
supplied-data analysis may claim, that is stated explicitly and separately.

## Instrument checks (C2 guard, run before trusting any number)

| Host | Division | Real | Junk-division fallback | Verdict |
|---|---|---|---|---|
| groupon.co.uk | `london` | `massage` = **458** | 431 | OK — real and distinct |
| groupon.pl | `warszawa` | `masaz` = **249** | 3 | OK — real and distinct |

`massage`/london = 458 is **identical to the 2026-08-05 reading**; `masaz`/warszawa moved 248 → 249.
The instrument is stable across days.

---

## P1 · Is a real-but-unstocked word as inert as gibberish? — **FALSIFIED, and replaced by something stronger**

**Predicted:** `paintball massage` returns the same count as `massage`, i.e. inert.
**Observed** (GB · london · 2026-08-06):

| query | count | vs `massage` (458) |
|---|---|---|
| `massage` | 458 | — |
| `paintball` | 12 | — |
| `paintball massage` | **470** | = 458 + 12 **exactly** |
| `skydiving` | 2 | — |
| `skydiving massage` | **460** | = 458 + 2 **exactly** |
| `xqzjw massage` | 458 | unchanged (gibberish still inert) |
| `helicopter` | 11 | — |
| `helicopter massage` | **418** | **below** `massage` — anomaly |

Set test, `massage` vs `paintball massage`, limit 100: 99 vs 99 ids, overlap **92**, Jaccard **0.868**,
`onlyInB` = `nationwide-paintball-1`, `paintball-networks-9`, `mse-paintball`, `velocity-paintball-1`,
`skirmish-paintball-2`.

**Verdict.** The prediction was wrong in a way that makes F1 *worse*, not weaker — but the honest
claim is narrower than "retrieval is a union", and the narrow version is the one to carry:

> **The result count is not a function of specificity, and it does not track whether the catalogue
> stocks the thing.** Adding a discriminating term sometimes adds exactly (`paintball` +12,
> `skydiving` +2), sometimes does nothing (`xqzjw` +0), and sometimes *subtracts*
> (`helicopter` −40).

**Do not claim union semantics.** Four recorded counterexamples contradict it, one of them in the
table above: `helicopter massage` **418 < 458**; the `dinosaur` pairs land *below* union;
`shark diving` (81) lands at *double* the union of its parts (39) — the latter two from the
2026-08-05 run recorded in `live_probe.js`. Whatever the engine is doing, it is not a set union, and
this run does not establish what it is.

The consequence survives the weaker claim intact, and it is the F1 mechanism: **the user has no
lever.** No word they add reliably narrows anything, so the system has no path to "we don't have
that" — and the paintball deals are blended *into* a massage result set rather than replacing it
(overlap 92/99, Jaccard 0.868).

**Anomaly, reproduced twice, cause CANNOT VERIFY:** `helicopter massage` = 418 < `massage` = 458,
while still injecting new `adventure-001-*` ids (overlap 94/99, Jaccard 0.904). A *decrease* that
still adds new documents is not explained by any simple set operation. Stated, not explained.

## P1b · Silent substitution — **OBSERVED, not inferred** *(not predicted; the most valuable result of the run)*

`FINDINGS.md` §3 tags "paintball returns escape rooms" as **CANNOT VERIFY** because the supplied log
has no query→deal mapping. Live Groupon has one. GB · london · 2026-08-06, exact result sets:

| query | total | what actually came back |
|---|---|---|
| `paragliding` | 2 | "London Cable Car + Uber Boat Hop-On Hop-Off 1 Day River Pass"; "London: London Cable Car + Uber Boat One Way River Thames Cruise" |
| `kitesurf` | 1 | "Portable Bartender Barista **Kit**" |
| `wingsuit` | 6 | "Automatic Flying Magic **Wings** for Kids"; "Vivo Folding Clothes Drying Rack with Height Adjustable Side **Wing**"; "Ariana Grande … 100ml Women's EDP"; "Senecio Angel **Wings** Potted Plants"; "Health **Ring**s Fitness Tracker Smart Ring"; "Dep London Stansted \| Greek Islands, 7 Nights" |
| `canyoning` | 1 | "Summit Ally Pally" |
| `skydive` | 2 | "Experience the Thrill of Skydiving – Solo or Duo, 7,000ft to 15,000ft"; "COSHH Online Course With Instant Certificate" |
| `trapeze` | 3 | "Cocktail Masterclass"; "Totally Musical Bingo"; "Pizza with a Drink at the Fun 3-Level Circus Glamour **Trapeze** Bar" |
| `quadbike` | 3 | "ATV / **Quad** (Drive / Experience)"; "VIP Desert Safari with BBQ Dinner & 30-Min **Quad Bike**"; "HOMCOM Kids Electric **Quad bike**" |

**Mechanism, visible in the titles:** the matcher decomposes the query and matches fragments —
`kitesurf` → *kit*, `wingsuit` → *wing* + *suit*. Combined with the union semantics from P1, this is
the whole of F1 in one picture: fragments, OR-ed, with no floor.

**F6 also appears live:** `quadbike` returns a **kids' electric toy quad bike** — Goods, not a local
experience — alongside two experiences. SPEC §3 cuts F6 because the supplied catalogue has no Goods;
that cut stands for the dataset, and this is the live evidence that the class is real.

## P2 · Does the multi-token diacritic penalty replicate? — **REPLICATES EXACTLY, GENERALISES NOT AT ALL**

PL · warszawa · 2026-08-06.

| pair | with diacritics | stripped | penalty |
|---|---|---|---|
| `masaż` / `masaz` | 272 | 249 | −8.5% *(2026-08-05: −8.8%)* |
| `masaż tajski` / `masaz tajski` | 162 | 95 | **−41.4%** *(2026-08-05: −41%)* |
| `masaż relaksacyjny` / `masaz relaksacyjny` | 215 | 112 | **−47.9%** *(2026-08-05: −48%)* |
| `zajęcia` / `zajecia` | 302 | 302 | **0%** |
| `żagle` / `zagle` | 73 | 73 | **0%** |
| `przedłużanie rzęs` / `przedluzanie rzes` | 9 | 9 | **0%** *(two tokens, two diacritic words)* |

**Verdict — split.** The three original pairs replicate to within 0.5pp a day later, so the
measurement was sound. But three new pairs, including a **two-token** one, show **no penalty at
all**. The effect is specific to the `masaż` token family, not a general multi-token rule.

**Consequence — and a decision taken deliberately: F2's range is left alone at (0.43, 0.52, 0.61).**
`BRIEF.md` pre-registered the falsifier as *"the penalty is flat, or single-token is worse."*
**Neither happened.** All three original pairs replicated to within 0.5pp, and single-token remained
the mildest case. So the prediction was confirmed as stated; what is unsupported is only its
*generalisation* to other token families, which the brief never pre-registered a response to.

Widening F2's range was the pre-registered response to a **failure**, and applying it to a partial
replication would import a live-catalogue result into a supplied-data measurement — the
catalogue-conflation trap `FINDINGS.md` §5e names. §5b's 42.3pp gap is measured in the supplied data and
nothing here touches it. **Recorded instead as a stated limit:** the live mechanism does not license
the claim that the diacritic penalty is general.

## 1.7(a) · Does PL narrow on more two-token queries? — **CONFIRMED, AND PL IS INCONSISTENT**

| query | parts | combined | behaviour |
|---|---|---|---|
| `kurs tańca` | `kurs` 312, `tańca` 4 | **4** | narrows to the rarer term exactly |
| `przedłużanie rzęs` | `przedłużanie` 10, `rzęs` 9 | **9** | narrows to the minimum |
| `masaż relaksacyjny` | `masaż` 272, `relaksacyjny` 75 | **215** | narrows below the larger part |
| `masaż gorącymi kamieniami` | 272, 22, 21 | **175** | narrows |
| `paznokcie hybrydowe` | `paznokcie` 3, `hybrydowe` 13 | **12** | ≈ the larger part |
| `joga tajski` | `joga` 7, `tajski` 28 | **31** | ≈ union (35) — **widens** |

**Verdict.** PL narrows on four of six pairs, which GB never did on any pair — but `joga tajski`
widens like GB. The defensible claim is therefore **not** "PL narrows". It is: *the same platform
applies different multi-term semantics in different markets, and is not internally consistent within
one market.* That is a stronger Part C line than the original hypothesis and it closes pending 1.7(a).

## P3 · Does live Groupon stock adrenaline in these cities? — **PARTIALLY CONFIRMED, AND MUCH WEAKER THAN PREDICTED**

**This entry was rewritten after Berlin and Paris were probed. The first version, from London alone,
claimed "confirmed, abundantly" and was wrong** — it rested on multi-word counts inflated by the very
P1 behaviour recorded above. Correcting it here rather than quietly is the point of the exercise.

**Multi-word queries — misleading, and this is why.** GB · london: `hot air balloon` 558,
`wing walking` 449, `gliding lesson` 173, `microlight flight` 112. Under P1, a multi-word query
returns roughly the union of its parts, so `hot air balloon` is dominated by *hot*, *air* and
*balloon* matching independently. **These are not 558 balloon rides and must not be read as supply.**

**Single-token queries — the honest instrument**, run across three cities and three hosts:

| GB · london | | DE · berlin | | FR · paris | |
|---|---|---|---|---|---|
| `skydive` | 2 | `fallschirmspringen` | **3** | `saut en parachute` | **3** |
| `paragliding` | 2 | `heissluftballon` | 1 | `parapente` | **0** |
| `bungee jumping` | 17 | `bungee` | 1 | `montgolfiere` | 5 |
| `falconry` | 5 | `hubschrauber rundflug` | 10 | `vol en helicoptere` | 18 |
| `abseiling` | 0 | `klettern` | 4 | `escalade` | 14 |
| `coasteering` | 0 | | | | |

C2 guards passed on all three: london 458 vs 431 · berlin 184 vs 39 · paris 444 vs 399.

**Verdict.** Live Groupon does stock *some* adrenaline — helicopter flights (10–18) and climbing
(4–14) are real inventory. But skydiving, ballooning and paragliding sit at **0–5 in every city
probed**. That is the *same regime* as the supplied dataset, not a contradiction of it.

**What this does to the bound on Part C — softer than the London-only reading suggested:**

- The supplied catalogue's **total** void (0 deals, 100% zero rate) is still an **exaggeration**, so
  it remains a modelling choice rather than a measurement.
- But it exaggerates a **real thinness**, not a fiction. The direction the analysis identifies —
  adrenaline demand meeting almost no adrenaline supply — **is visible in production**.
- Part C **may** now say: *this pattern is not merely an artifact of the supplied data; live Groupon
  shows the same shape at less extreme magnitude.*
- Part C still **may not** put a number on real Groupon's inventory gap from this run, and still may
  not recommend specific vendor acquisition in a named city.

**The methodological lesson is worth more than the result**, and belongs in Part C's "what the tools
got wrong": *the first pass measured supply with multi-word queries and read abundance into a number
that P1 had already shown to be an artifact.* One probe contradicted another probe in the same
session, and only checking a second and third city surfaced it.

## P4 · Does live ever return exactly 3? — **CONFIRMED. This rewrites a number.**

GB · london, N = 33 single- and multi-token queries across two batches.

- **`quadbike` = 3** and **`trapeze` = 3**.
- Low-count distribution is smooth: 0 (×6), 1 (×4), 2 (×2), **3 (×2)**, 5, 6, 7, 8, 10, 17.
- Independently, the PL invalid-division fallback for `masaz` also returns **3** — the trap already
  noted in `live_probe.js`'s header, unconnected to P4 until now.
- **Two more found while probing P3 on other hosts:** `fallschirmspringen`/berlin = **3** and
  `saut en parachute`/paris = **3**. So exactly-3 now appears on **three different hosts**
  (`.co.uk`, `.de`, `.fr`), which removes any "GB-specific quirk" reading.

**On the sample size, because `QUERIES.md` pre-specified N=60/host and this run used N=33 on one
host.** That design exists because *under-sampling is how a null result gets over-claimed* — with a
small N, "3 never appeared" could just mean the low-count regime was never reached. **That risk does
not apply here, because this is a positive result.** Two observed 3s plus a third (the PL fallback)
establish existence; no additional N can weaken an existence claim. The low-count regime was
demonstrably reached — 0, 1 and 2 all appear with frequency. **Had 3 been absent, this run would be
`inconclusive` and reported as such.**

**Verdict.** Live Groupon returns exactly 3 routinely. The supplied data's 0, 1, 2, → 4 gap across
**8,997** searches with not a single 3 is therefore a **generator artifact, not a ranking cutoff**.

**F5 is a mislabelled class.** Its 40% recoverability assumption rested entirely on "no query returns
exactly 3, which suggests a cutoff". That inference is now dead.

## P5 · Does live widen radius with distance framing? — **THE INSTRUMENT EXISTS AND IS EMPTY WHERE IT MATTERS**

Every `BrowseDealFeed` call returns two facets for free:

- `distance`, cumulative, for `massage`/london of 458: **1km 11 · 5km 136 · 10km 228 · 20km 302 ·
  50km 371 · 100km 403**
- `locations`, per town: **London 154 · Perivale 14 · Croydon 10 · Basildon 7 · Romford 7 ·
  Ashford 7 · Slough 5 · Winnersh 5** (154 towns in total for the FR equivalent)

For **thin** queries both facets are empty: `paragliding` returns totalCount 2 with **0 results at
every radius** including 100km, and **no locations facet at all**. Same for `canyoning`, `kitesurf`,
`wingsuit`.

**Verdict.** The platform computes per-town and cumulative-distance counts on every single call, and
they go empty exactly for the queries where radius widening would be the useful answer. Live does not
widen radius for thin queries — **it substitutes instead**. So F3's proposed fix is *not* table
stakes, and the prototype's version is worth more, not less. P5 falsified in the direction that helps.

Note also that `paragliding` shows **2 results that are in no distance bucket at all**. The system
has the information to know it has nothing near the user, and returns results anyway.

## P6 · The `SuggestedSearchQueries` 500 — **REPLICATED on a different host and a different day**

www.groupon.pl · 2026-08-06: `masaz`, `mas`, `skydiv` → `Cannot read properties of undefined
(reading 'logError')`. `masaż` → valid response, `items: []`.

Original observation was groupon.co.uk · 2026-08-05, 5/5 errors. Now cross-host **and** cross-day, so
it is no longer a single-session artifact and is quotable as a production defect: the layer where
spell correction and query understanding live returns errors or nothing.

---

## NEW · What the API does not return *(not predicted; directly answers the 004 brief's "what it doesn't return")*

`BrowseDealFeed` response for `masaz tajski` · warszawa · totalCount 95:

- `data.browseDealFeed` → `cards`, `facets`, `pagination`, `browseProps`
- `pagination` → `limit`, `offset`, `nextOffset`, `feedToken`, `totalCount`
- `cards[n]` → `id, uuid, optionId, url, title, adId, categoryGuid, prices, options, displayOptions,
  merchant, promotion, cashBack, limitedSale, imageUrls, rating, badges, discountPercentage,
  locationsSummary, icon, flags, invalidateAt`

**Absent from the entire response:** any relevance or match score · any matched-term or
query-understanding field · any spell-correction / "did you mean" field.

**Why this matters more than it looks.** The client receives a count and a list, and **cannot
distinguish a deal that genuinely matched from padding**. That is precisely the limitation of the
supplied dataset — `results_shown` is a count, with no query→deal mapping. So the dataset's central
weakness is not an artifact of the exercise: **it faithfully reproduces what the production API
itself exposes.** That reframes the honesty caveat into a platform ask — *expose match provenance* —
which is a concrete answer to the brief's "what do you need from the platform teams who own search".

---

## What this changes

| Where | Change |
|---|---|
| `002-recoverability/notebook.py` | **DONE — F5 set to (0.00, 0.00, 0.00), was (0.10, 0.40, 0.70).** The "no 3s ⇒ ranking cutoff" inference is dead (P4). `classify.py`'s F5 predicate is a **residual** (stocked · failing · not F2 · not F3), not a cutoff test, so the 353 dead ends stay a real population with no known cause — a second BASELINE. Bucket kept, label and recoverability withdrawn. |
| `002-recoverability/notebook.py` | **F2 deliberately NOT changed** — the pre-registered falsifier did not fire. See P2 above. |
| `FINDINGS.md` §3 | F1 silent substitution moves from **CANNOT VERIFY** to **VERIFIED (live catalogue only)** — with exact result sets. The supplied-data claim stays inference. |
| `FINDINGS.md` §1 | The missing `results_shown = 3` is resolved: **generator artifact**. Closes half of pending 1.6 and known issue #4. |
| `001-part-b/SPEC.md` §3 | F1's behaviour is *better* justified (union semantics + fragment matching), F3's is *better* justified (P5 falsified), F5's is *worse* justified. |
| Part C | P3 bounds the supply-void claim — but **less tightly than the London-only first pass suggested.** Live adrenaline is thin in all three cities probed, so the supplied catalogue *exaggerates a real thinness* rather than inventing one. Part C may say the pattern is not merely a synthetic-data artifact; it may still not size real Groupon's gap or name a city for vendor acquisition. See the rewritten P3. |
| Pending 1.7(a), 1.7(b) | Both closed. |

**Does the ~18% conclusion survive?** **The direction strengthens and the number changes — 18% is now
wrong and must not be quoted.** Re-run 2026-08-06 with F5 at zero:

| | before | **after P4** |
|---|---|---|
| search-fixable | 59 purchases/mo | **36** |
| range across assumptions | 22 – 88 | **16 – 48** |
| supply-void ceiling (unchanged) | 271 | 271 |
| **search's share of the recoverable total** | **17.9%** | **11.8%** |
| share, pessimistic → optimistic | 7.4% → 24.5% | **5.6% → 15.1%** |

F4 is zero by construction inside the supplied data and is untouched, so the conclusion's *direction*
was never sensitive to the assumptions — that was the point of the sensitivity cell. P4 moved one
assumption to its floor, which lowered the numerator and **strengthened** the conclusion: even at the
optimistic end, search is now 15% of the opportunity rather than 25%.

**Propagation required — this is the repo's known failure mode** (the 11.5 → 11.4 → 299 episode, a
stale rate living inside a derived figure). "Search work is ~18%" is one of the two things
`INDEX.md` says Part C must carry, and it is injected into every session by the `SessionStart` hook.
Every copy must move to **~12%**: `INDEX.md` Now/Next, `FINDINGS.md`, and any SPEC copy quoting it.

## Scope actually run, against what `QUERIES.md` scoped

`QUERIES.md` offered three options and recommended option 2 (capitals only, ~75 min). **This run is
closest to option 3** (~45 min, the original budget): P1, P3 and P4 in full — the three that change
a number or a claim — with P2, P5 and P6 collected alongside.

| | Scoped | Run |
|---|---|---|
| Hosts | 5 (`.co.uk .de .fr .es .pl`) | **2** — `.co.uk`, `.pl` |
| Divisions | 20 cities, step 0.2 | **2** — `london`, `warszawa`, both C2-guarded |
| P4 sweep | N=60/host | **N=33**, one host — sufficient for a *positive* result, see P4 |
| P5 | 5 rows incl. `.de`/`.fr` | distance + locations facets on GB only |
| P6 | per-host across 5 hosts | `.pl` only this run; `.co.uk` from 2026-08-05 |

**Not run, and therefore not claimed:** DE, FR, ES hosts; the 18 non-capital divisions; P5 row 5.5
(the *% of results beyond 20 km* ratio, which needs a thin/dense pair on the same host); P2's DE/FR/ES
equivalents.

## Limits of this run

- Single session, single day, one division per market, no account. Counts were stable on repeat;
  **ordering was not** — card-level claims need repeated loads.
- Counts are inflated by union semantics (P1). They measure *what the engine returns*, not *how much
  relevant inventory exists*. Do not read `hot air balloon` = 558 as 558 balloon rides.
- GB and PL only. DE/FR/ES not probed this run.
- P6's autocomplete failure could be geo- or session-specific despite replicating cross-host.
