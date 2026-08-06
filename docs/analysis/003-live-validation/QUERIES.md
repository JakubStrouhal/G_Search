# Live validation — the executable layer under P1–P6

Written 2026-08-06. **Companion to `BRIEF.md`, not a replacement.** `BRIEF.md` owns the
predictions and the falsifiers; this file owns the setup, the exact query strings, and the GraphQL
contract they run against. Every query row carries the P-number it serves. **A query that does not
serve a P is either a new P added to `BRIEF.md`, or it is out** — this repo's recurring failure is
the second parallel artifact (two `CONCEPTS` maps, two supply-void counts, four status copies).

Harness: `docs/analysis/live_probe.js`, extended to v2 on 2026-08-06 with the functions used below.

---

## 0. What the GraphQL actually is — verified, not assumed

Verified 2026-08-06 by dumping one full raw response (61 KB) and reading the field tree, rather
than by reading the probe. **The old probe reads exactly one number out of that response**
(`pagination.totalCount`) and discards the rest, so "what does the API return" could not have been
answered from it.

**Endpoint.** `POST /mobilenextapi/graphql`, same-origin, `credentials: 'include'`. Operation
`BrowseDealFeed`, persisted-query hash `b035b25d…f429`. Query term travels as
`filters: [{key:'query', subKey:null, value:{static:'<term>'}}]`; location as `division: '<key>'`.

**Response shape** — `[{data:{browseDealFeed:{cards, facets, pagination, browseProps}}}]`:

| Field | Contents |
|---|---|
| `pagination` | `{limit, offset, nextOffset, feedToken, totalCount}` — `totalCount` is the exact integer the UI buckets as "400+" |
| `cards[]` | 23 fields incl. `id` (stable merchant/deal slug — **the join key**), `uuid`, `url`, `title`, `merchant`, `rating`, `prices`, `locationsSummary`, `badges`, `flags` |
| `facets[]` | 13: `brand, categories, categories_flat, distance, locations, price, rating, amenities, category_icons, giftable, gifting_flag_sections, bookable, sort` |
| `browseProps` | `{pageName, pageType, division, breadcrumbs, categoryPath, …}` |

### Two instruments we were not reading, free on every call

- **`facets.locations`** — per-town result counts *for this query*. `massage`/`paris` returns 154
  towns: Paris 159, Saint-Maur-des-Fossés 12, Pontault-Combault 5… This measures geographic spread
  directly. **F3 stops being an inference.**
- **`facets.distance`** — a *cumulative* distance histogram with counts. `massage`/`paris`:
  19 within 1 km, 198 within 5 km, 272 within 10 km, out of 444. So ~170 results sit beyond 20 km.
  This is the "thin sets get padded with filler" observation (`PLAN.md` §4 Finding 2, the Devon
  skydive 141 miles from London) turned into a **number per query**.

Both are new evidence channels for Part A/B and cost nothing extra to collect. Record them.

### Constraints that invalidate reasonable-looking probe shapes

| # | Constraint | Consequence |
|---|---|---|
| **C1** | **`offset` is silently ignored** when `feedToken: null` / `isFetchMore: false`. Verified: `offset:20` and `offset:400` both return page 1; `offset:600` against `totalCount:458` still returns cards | Deep paging needs `feedToken` echoed back with `offset:nextOffset` and `isFetchMore:true`. That works — 0 overlap between consecutive pages. Use `pageAll()`. Anything that naively walks `offset` is measuring page 1 repeatedly |
| **C2** | **An invalid `division` does not error.** It falls back to a default scope, and `browseProps.division` **echoes what you sent** — so the echo is not confirmation. On `.fr`: `paris` → 444, while `not-a-division` → 399 *and* `zzzzqqq` → 399, with an identical locations facet | A typo'd division returns a plausible, wrong, self-consistent number. This is the `warsaw`/`warszawa` trap and it is **worse than documented — there is no error signal at all**. Run `divisionControl()` per host before trusting anything |
| **C3** | `limit` honoured to ~200, returns one fewer than asked (100→99, 200→199) | Cap ID-set comparisons at ~199 unless paging. Don't read meaning into the off-by-one |
| **C4** | Ordering is unstable across identical calls; counts are stable | Compare ids as **unordered sets**. Never compare positions |
| **C5** | Same persisted hash resolves on `.co.uk`, `.de`, `.fr` (verified) | `.es` / `.pl` unconfirmed — step 0.1 below |
| **C6** | Same-origin + session cookies | **Five browser sessions, one per host.** Not one flat matrix. Consent banners on `.de`/`.fr`/`.es` may gate the SPA; decide accept/decline **once** and keep it identical across all five, or it is an uncontrolled variable |
| **C7** | **Counts drift ±2 within a day.** `massage`/`london` read 458 twice, then 460 an hour later | Pin the date on every figure. Never read a ±2 difference as an effect. Diffs of interest here are 40%+ |
| **C8** | `totalCount` **does not saturate** — paging to exhaustion collected exactly 460 unique ids against `totalCount` 460 | Comparisons in the 400s are valid, and the integer is a real count rather than an estimate |
| **C9** | `limit: 1` returns a valid `totalCount` with 1 card | The P4 sweep at `limit:1` is safe — verified, not assumed |

### The correction this forces to a load-bearing claim

`xqzjw massage` = `massage` = 458 is the single piece of *observed* evidence for F1, and
`001-part-b/SPEC.md` §3 puts `458 = 458` on screen as what moves F1 from CANNOT VERIFY to observed.
**A count equality is equally consistent with a different set of the same size.** That upgrade was
not earned by the count alone.

**Now it is — exhaustively.** Verified 2026-08-06, division `london`: both queries paged to
exhaustion via `feedToken` (5 pages × limit 100) yield **460 unique ids each, Jaccard 1.0000, zero
ids in one and not the other.** Not a top-N sample — the whole result set. Two controls make that
readable:

- **Noise floor.** `massage` vs `massage` at limit 100 → Jaccard 1.0 **and identical ordering**. So
  membership does not drift between identical calls, and the cross-query result is not luck.
- **Ranking vs membership.** `massage` vs `xqzjw massage` returns the same ids in a **different
  order**. So `xqzjw` *does* reach the scorer and perturbs ranking — it simply cannot add, remove or
  filter a single document. **"The word cannot change what you get, only what order you get it in"
  is the sharper and more defensible statement of F1**, and the one to put in UI copy.

Every P1 row below is therefore a `compare()` call, not a `total()` call — and `compare()` can
falsify P1 in a way counting structurally cannot.

---

## Step 0 — setup, per host. Do not skip; C2 makes skipping silent

| # | Task | How | Blocks |
|---|---|---|---|
| 0.1 | Confirm the persisted hash resolves on `.es` and `.pl` | Paste probe, run any `feed()`. If `PERSISTED_QUERY_NOT_FOUND`, re-capture from the Network tab per host | All ES/PL rows |
| 0.2 | **Harvest and verify the division key for each of the 20 dataset cities** | `divisionControl('<key>')` per host — the *only* thing that earns a VERIFIED tag. Candidate source for the rest: the site's own location-picker request, or `facets.locations` values | Everything — C2 |
| 0.3 | Fix the consent decision and record it | Decline non-essential, identically on all five hosts | Cross-market comparability |
| 0.4 | Record the fallback number per host | It is the tell that a division silently failed mid-run | All rows |

**Division status — VERIFIED means the fallback control was actually run, not that a number came
back.** Two of the four "known" keys had never been tested against their host's fallback:

| Market | Division | Real | Host fallback | Status |
|---|---|---|---|---|
| GB | `london` | 458 | 431 | ✅ **VERIFIED** — distinct, fallback stable across two junk strings |
| FR | `paris` | 444 | 399 | ✅ **VERIFIED** — distinct, fallback stable |
| DE | `berlin` | 184 | — | ⚠️ number observed, **control not run** |
| PL | `warszawa` | 248 | — | ⚠️ distinguished from `warsaw` (3), **but never from fallback** |
| ES | `madrid` | — | — | ⬜ unprobed |

Note the fallback differs per host (GB 431, FR 399), so it must be measured per host, not assumed.

**Dataset cities needing division keys** (4 per market, from `search_log.csv`) — 0.2 is not done
until all 20 are either verified or explicitly marked "not probed, using capital only".

---

## The query tables

**Every row records:** `market · division · exact query string · date · totalCount · locations
facet · distance facet`, plus **which catalogue it describes**. Live ≠ the supplied dataset —
`BRIEF.md` and `PLAN.md` §7 both flag conflating them as the trap. All rows below are **LIVE**.

Results column deliberately blank — fill during the run.

### P1 · F1: is a real-but-unstocked word inert? — `compare()`, sets not counts

Predicts the discriminating term does not constrain. **Falsified if the count drops or Jaccard < 1.**

⚠️ **The obvious probe terms don't work live, and this is itself a finding.** The plan was
`paintball massage` and `sushi massage`, on the dataset's basis that paintball and sushi are stocked
nowhere. **Live GB stocks both** — `paintball`/london returns **12 genuine paintball deals**
("Paintballing for Five Players", "Half-Day Paintball Sessions for Groups"), `sushi` returns **28**
genuine sushi deals. So they are not zero-match tokens live, a union would be ~470, and the row
would measure expansion rather than inertness.

This is the live-vs-supplied catalogue line doing real work: **the F1 examples in `FINDINGS.md` §3
are properties of the synthetic catalogue only.** Part C must not imply Groupon lacks paintball.

| # | Host | Division | Query A | Query B | Expect | Result |
|---|---|---|---|---|---|---|
| **1.0** | .co.uk | london | — | — | **Find 2–3 real English words returning 0.** Needed before 1.2/1.3 exist. Try niche experiences: `falconry`, `bobsleigh`, `curling lesson`, `hot air balloon ride`. Any that returns 0 is a valid inert-token candidate | |
| 1.1 | .co.uk | london | `massage` | `xqzjw massage` | ✅ **done, exhaustive**: 460/460 ids, Jaccard 1.0000, order differs | ✅ |
| 1.2 | .co.uk | london | `massage` | `<1.0 term> massage` | Jaccard 1.0 if P1 holds. **The real-word version of 1.1** — gibberish may be handled differently from a real out-of-catalogue word | |
| 1.3 | .co.uk | london | `massage` | `paintball massage` | Now an **expansion** row, not inertness: paintball has 12 of its own. Union ≈ 470 | |
| 1.4 | .co.uk | london | `escape room` | `xqzjw escape room` | Second head — controls for `massage` being special | |
| 1.5 | .de | berlin | `massage` | `xqzjw massage` | " | |
| 1.6 | .fr | paris | `massage` | `xqzjw massage` | " | |
| 1.7 | .es | madrid | `masaje` | `xqzjw masaje` | " | |
| 1.8 | .pl | warszawa | `masaz` | `xqzjw masaz` | Count already 248=248; **set untested** | |
| 1.9 | .co.uk | london | `diving` / `shark` | `shark diving` | The expansion anomaly (29+10 → 81). Are the 81 a superset? | |

Row 1.0 is a genuine blocker for 1.2 and is cheap. Row 1.9 tests *expansion* rather than inertness —
`PLAN.md` §4 shows multi-term retrieval is neither union nor intersection, and the platform ask
depends on it being two problems.

**Record `cards[].title` and `cards[].categoryGuid` on every P1 row.** `facets.categories` comes back
empty, but the cards carry both, so **substitution content is directly observable live**.
`FINDINGS.md` §3 tags "paintball returns escape rooms" CANNOT VERIFY *in the supplied data* — live,
you can see exactly what a no-match query is answered with. That is free on calls already being made
and makes `SPEC.md` §8's side-by-side ("what today's system would have shown") concrete instead of
schematic.

### P2 · F2: does the multi-token diacritic penalty replicate across markets?

Observed PL: single-token −8.8%, multi-token −41%/−48%. Predicts the same shape in DE/FR/ES.
**Falsified if flat, or if single-token is worse.** This is the expensive one — F2's 52% is the
notebook's only measured anchor.

| # | Host | Division | Correct | ASCII/stripped | Tokens | Result |
|---|---|---|---|---|---|---|
| 2.1 | .pl | warszawa | `masaż` | `masaz` | 1 | ✅ 272 / 248 = −8.8% |
| 2.2 | .pl | warszawa | `masaż tajski` | `masaz tajski` | 2 | ✅ 162 / 95 = −41% |
| 2.3 | .pl | warszawa | `masaż relaksacyjny` | `masaz relaksacyjny` | 2 | ✅ 215 / 112 = −48% |
| 2.4 | .pl | warszawa | `paznokcie hybrydowe` | — | 2 | Two-token PL control, task 1.7(a) |
| 2.5 | .pl | warszawa | `zabieg na twarz` | — | 3 | Does narrowing worsen with token count? |
| 2.6 | .de | berlin | `rückenmassage` | `ruckenmassage` | 1 | |
| 2.7 | .de | berlin | `haare färben` | `haare farben` | 2 | Dataset query |
| 2.8 | .de | berlin | `gesichtsbehandlung männer` | `gesichtsbehandlung manner` | 2 | |
| 2.9 | .fr | paris | `beauté` | `beaute` | 1 | |
| 2.10 | .fr | paris | `massage thaïlandais` | `massage thailandais` | 2 | |
| 2.11 | .fr | paris | `extension de cils` | — | 3 | Dataset query |
| 2.12 | .es | madrid | `depilación` | `depilacion` | 1 | |
| 2.13 | .es | madrid | `depilación láser` | `depilacion laser` | 2 | |
| 2.14 | .es | madrid | `masaje relajante` | — | 2 | |

**Also record for 2.4/2.5/2.11/2.14:** does adding a matching term *narrow* (PL behaviour) or
*widen* (GB behaviour)? That GB/PL divergence is `PLAN.md`'s candidate Part C headline and task
1.7(a) is exactly this confirmation. Compare each multi-token count against its head term alone.

### P3 · F4: does live Groupon stock adrenaline in these cities?

Predicts **yes, abundantly**. If confirmed — the likely case — the supplied catalogue's void is a
**modelling choice, not a description of Groupon's assortment**, which hard-bounds what Part C may
claim. Queries are the dataset's actual 100%-zero pairs, so the mapping back to Part A is exact.

| # | Host | Division | Query | Dataset says | Result |
|---|---|---|---|---|---|
| 3.1 | .co.uk | london | `skydiving` | 91/91 zero | ✅ **2** — and one is a workplace-safety course |
| 3.2 | .co.uk | london | `helicopter tour` | 100/100 zero | |
| 3.3 | .co.uk | london | `hot air balloon ride` | 94/94 zero | |
| 3.4 | .co.uk | london | `supercar track day` | 87/87 zero | |
| 3.5 | .co.uk | london | `shark diving` | 80/80 zero | ✅ 81 (2026-08-05) |
| 3.6 | .de | berlin | `fallschirmspringen` | 64/64 zero | |
| 3.7 | .de | berlin | `hubschrauber rundflug` | 65/65 zero | |
| 3.8 | .de | berlin | `wildwasser rafting` | 75/75 zero | |
| 3.9 | .fr | paris | `saut en parachute` | 81/81 zero | |
| 3.10 | .es | madrid | `paracaidismo` | 86/86 zero | |
| 3.11 | .es | madrid | `rafting` | 88/88 zero | |
| 3.12 | .pl | warszawa | `lot balonem` | 57/57 zero | |

⚠️ `skydiving`/London already returns **2**, not hundreds. If that pattern holds across 3.2–3.12,
P3 is *partially falsified* and the picture is more interesting than "live stocks everything": it
would mean live GB is also thin on adrenaline, and the dataset exaggerates rather than invents. Do
not narrate that away in either direction — record the counts.

### P4 · F5: does live search ever return exactly 3? — **needs a sweep, not a matrix**

This is a **distribution** question. A hand-picked list cannot answer it, and it is the check that
moves the notebook's central estimate from ~59 to ~36 purchases/month. Use `histogram()`.

**Stated design — decide N before running, and record it with the result:**

- **N = 60 queries per host** (300 total), drawn as: 20 dataset queries + 20 deliberate
  long-tail/typo strings + 20 rare two-token compounds. Thin queries are where 1/2/3 live.
- Report the full low-count distribution (0–10), not just whether 3 appeared.
- **What a null result licenses:** with N=60 per host, absence of 3 is *suggestive*, not proof.
  If counts 1, 2 and 4 all appear with reasonable frequency and 3 never does, that is a genuine
  cross-catalogue pattern worth Part C. If 1 and 2 are themselves rare, N was too small and the
  honest verdict is **inconclusive** — say so rather than claiming the gap.
- At ~1.5 s pacing, 300 queries ≈ **8 minutes of requests**. This is the cheap part; building the
  query list is the work.

### P5 · F3: radius widening — now measurable via `facets.distance`

Predicts live surfaces nearby-city inventory with distance stated. The distance facet answers this
**quantitatively** rather than by screenshot.

| # | Host | Division | Query | Record | Result |
|---|---|---|---|---|---|
| 5.1 | .fr | paris | `massage` | Cumulative distance curve | ✅ 19@1km / 198@5km / 272@10km / 444 total |
| 5.2 | .co.uk | london | `skydiving` | Where do the 2 sit? | Devon result ≈141 mi (2026-08-05, UI) |
| 5.3 | .de | berlin | `fallschirmspringen` | Distance curve if non-zero | |
| 5.4 | .co.uk | london | `escape room` | Dense-query control | |
| 5.5 | any | any | thin vs dense pair | **The metric: % of results beyond 20 km.** Thin queries should skew far if padding is real | |

Row 5.5 is the deliverable: a single ratio that distinguishes "we have 458 nearby" from "we have
458, most of them nowhere near you". That is F1/filler made measurable, and nothing in Part A
currently measures it.

### P6 · `SuggestedSearchQueries` — re-check before quoting

Observed 2026-08-05: `INTERNAL_SERVER_ERROR` on 5/5 GB queries. **One day, one session, one client.**

| # | Host | Action | Result |
|---|---|---|---|
| 6.1 | .co.uk | `probeSuggest()` — same 4 queries, different day | |
| 6.2 | .de / .fr / .es / .pl | `probeSuggest()` — is it GB-only or global? | |
| 6.3 | — | If still 500: capture the exact error + date, and **only then** may Part C quote it | |

Per-host is the addition: a global 500 and a GB-only 500 are different claims.

---

## Scoping — flag before you start

`BRIEF.md` budgets **~45 minutes**. This list is **not** a 45-minute job: ~60 comparison/count rows
plus a 300-query P4 sweep plus step 0 across five hosts is realistically **2.5–4 hours**, most of it
step 0.2 (division keys) and building the P4 query list.

**That is a scoping call, not something to absorb by quietly under-sampling** — under-sampling P4 is
exactly how a null result gets over-claimed. Three honest options:

1. **Full run** (~3 h). Everything above. Justified only if P3/P4 outcomes will actually change the
   build, which per `BRIEF.md` they will.
2. **Capital-cities-only cut** (~75 min). One division per market, P4 at N=30/host, skip 0.2 for
   the other 15 cities and state the limit. **Recommended** — it preserves every falsifier and
   loses only geographic breadth.
3. **P1 + P3 + P4 only** (~45 min, honours the original budget). These three are the ones that
   change a number or a claim. P2 already has three measured PL pairs; P5 now has an instrument and
   can be collected passively from whatever calls do run.

Option 2 unless you say otherwise. Either way: **record N and record what was skipped** — a
coverage claim that quietly rests on 12 queries is the failure mode this whole exercise grades.

---

## Done looks like

Unchanged from `BRIEF.md` §"Done looks like", plus:

6. `live_probe.js` v2 constraints C1–C6 confirmed or corrected on a second run.
7. The **set-identity** result (Jaccard 1.0) written into `FINDINGS.md` §3 and
   `001-part-b/SPEC.md` §3, replacing the count-equality phrasing — this upgrades F1's evidence
   from CANNOT VERIFY toward observed, which the count alone did not.
8. `facets.distance` / `facets.locations` either adopted as a new evidence channel or explicitly
   parked with a reason.
