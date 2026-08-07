# INDEX — state, queue, defects, decisions

**This file wins on status.** Nothing else states it. `README.md` is grader-facing, `CLAUDE.md` is
agent ops, `docs/analysis/PLAN.md` is reasoning, `FINDINGS.md` owns the numbers — none of them
carry a status table any more, by design.

**State, not history.** Every section is overwritten in place and pruned when resolved. Nothing is
append-only. History is `git log`, which cannot drift. The one bounded exception is *Decisions*
below: a fixed-capacity ring buffer, six rows, oldest deleted on write.

Written by `/wrap` and by each pipeline command; the *Now / Next* and *Decisions* blocks are
injected into every new session by the `SessionStart` hook.

**Statuses:** ⬜ not started · 🟡 in progress · ✅ done · 🔴 blocked · ⚪ parked

## Now / Next

<!-- state:start -->
- **Phase:** Part A is done, **validated against live production** (P1–P6) and **re-spined**
  (2026-08-06) around one question — *when a search failed, where was the answer?* Its artifact is
  `004-data-story/outputs/explainer.html`. Part B has an approved spec (`001-part-b/SPEC.md`) and an
  empty stack (`005-stack-init/`: local Supabase boots, **zero migrations, zero tables**). Part C not
  started. **B and C are the whole remaining risk.**
- **The spine, and it is what Part C should open with.** Over all 4,720 dead ends:
  **nowhere in the market 43.2% · the user's own city 32.2% · another city 3.1% · can't tell 21.5%**.
  Four buckets, four owners; F1–F6 nests inside (`nowhere` **is** F1 ∪ F4, asserted in code).
  **Quote the `nowhere` band [43.2%, 64.7%], never one end.** `FINDINGS.md` §5f is the source for
  these and for the permutation test that gated them — if a number here disagrees with §5f, §5f wins.
- **Top next actions (ranked):**
  1. **Build Part B** from `001-part-b/SPEC.md` — §6 architecture, §10 build order. Step 1 is
     Supabase migrations + seeds; **step 4 (threshold sweep) gates all UI work**. Budget tension is
     real and stated in §6: log the real hours.
  2. **Part C.** Draft after B exists. Open with the bucket split, then the language test; the 52.5%
     is support, not the headline. Ready-made "what the AI tools got wrong" examples are in
     `FINDINGS.md` § Corrections — use one of those, not a generic line.
  3. Remaining notebook angles: demand–supply divergence (6.2), top-50 stat into FINDINGS (6.4).
- **Two things Part C must carry:** the **language test** (`FINDINGS.md` §5b) and the
  **recoverability split** (§5e) — search work is a *minority* of the recoverable opportunity, well
  behind the supply void. **The old ~18% / 59-purchases figures are dead.** Every way of tightening
  the search side lowers it further; publish the most generous and say the others exist.
- **Deliberately not doing:** any more Part A hardening. B is still empty.
<!-- state:end -->

## Decisions — last 6, newest first, oldest row deleted on write

<!-- decisions:start -->
| Date | Decision | Why |
|---|---|---|
| 2026-08-06 | **Embed 75 services, not 236 — city and market filter in SQL (D-A, deviates from SPEC §6)** | City is a structured filter; in the vector it shifts scores for reasons nobody can audit |
| 2026-08-06 | **`.claude/agents/` restored — be/fe/reviewer teammates + `/execute:team`; reverses b48e3fb** | Part B spans two lanes. Agent teams need definitions; the deleted folder held only a README |
| 2026-08-06 | **Operating docs cut to four files; whole tree committed to a branch first** | Nine places, three taxonomies, loaded every session. One commit made deletion unrecoverable |
| 2026-08-06 | **Explainer re-spined on "where was the answer?"; F1–F6 nests inside** | Six classes is more than a reader holds, and *where* assigns an owner where *why* does not |
| 2026-08-06 | **F3's "geographic" diagnosis withdrawn, range kept at 25%** | 6 of 321 dead ends are really another-city. Re-deriving lowers the headline; publish the generous one |
| 2026-08-06 | Stack: **imperative migrations, local-only, publishable key** — not declarative, not linked | Budget; nothing before hosting needs a remote. Anon keys are compatibility-only per Supabase |
<!-- decisions:end -->

*Newest row goes under the header; the bottom row is deleted in the same edit. The hook injects
the top three into every session, so keep Decision ≤15 words and Why ≤20 — see
`.claude/decision-row.md`. Durable decisions live in the artifact they govern, not here.*

## Board

| Part | What | Status | Where |
|---|---|---|---|
| **A** | What is broken — analysis with the numbers | ✅ done and reconciled | `docs/analysis/{validate,classify,language_test}.py`, `FINDINGS.md`, `outputs/` |
| **A′** | Live production reconnaissance | ✅ done | `docs/analysis/PLAN.md` §4, `live_probe.js` |
| **A″** | Live validation of P1–P6 (pre-registered) | ✅ done 2026-08-06 | `003-live-validation/RESULT.md` |
| **A‴** | Data story — business-readable Part A + interactive explainer | ✅ done 2026-08-06 | `004-data-story/`, deliverable is `outputs/explainer.html` |
| **B** | Working clickable prototype | 🟡 spec approved; **stack init 4/11 done** (local Supabase boots, empty by design) | `docs/analysis/001-part-b/SPEC.md`, `005-stack-init/BRIEF.md` |
| **C** | Writeup, 2 pages + tools log | ⬜ not started | — |

## Pending

| # | Item | Status | Note |
|---|---|---|---|
| 1.6 | Write down positions on the two unresolvable items | 🟡 | **Half closed 2026-08-06.** `results_shown = 3` is settled — generation artifact, proven against the live catalogue (`FINDINGS.md` §1). Paintball's conversion still open. Fold the synthetic-data chi-square in here |
| ~~1.7~~ | ~~Live-recon follow-ups~~ | ✅ | **CLOSED 2026-08-06.** (a) PL narrows on 4 of 6 two-token pairs (`kurs tańca` 312+4→4) but `joga tajski` widens — PL is *inconsistent*, which is the stronger claim. (b) The 500 replicated on `groupon.pl`, a different host and day. Both in `003-live-validation/RESULT.md` |
| 3.4 | Write the Option A/B/C rejection reasoning into Part C | ⬜ | Decided in `PLAN.md` §3-equivalent; the brief asks for it explicitly |
| 4.0 | Stack init per `005-stack-init/BRIEF.md` | 🟡 | **Steps 1–4 and 6–9 done 2026-08-06.** Local stack boots with **zero migrations**; `web/app` (Vue3+Vite+TS) builds and its health check reads PostgREST 200 + a `PGRST205` round trip, verified in-browser. Step 5 (remote link) **deferred — local-only until hosting**. Left: **10** — **dropped 2026-08-06**, superseded: Supabase's own skills are installed at `.claude/skills/supabase*/`. **11** (doc sweep) closed by the same-day simplification pass. `.claude/agents/` was removed in `b48e3fb` and **restored 2026-08-06** with three build roles (`be-builder`, `fe-builder`, `reviewer`) — see Decisions |
| 4.1 | Build Part B per `001-part-b/SPEC.md` §10 | 🟡 | **Step 1 DONE 2026-08-06 — schema *and* mechanical seeds.** `supabase/build_seed.py` generates `seed.sql`; `db reset` applies migration + seed in one command. Loaded and **verified in the DB against Part A**: 20 cities · 568 deals · 75 services · 75 service_concepts · 751 query_classes · 1,322 demand_events; absent **437** = F4 178 + F1 259, stocked+plausible **314**, dead ends **4,720**, another_city **145**, GB London adrenaline **222**, demand `n` sums to **8,997**. `city_spread` made **nullable** — null on 571 rows means *not computable*, which is not 0.0. Migration `supabase/migrations/20260806220629_part_b_initial_schema.sql`: 7 tables, 2 `security_invoker` views, RLS + explicit grants, advisors clean, verified after a full `db reset`. **Security fix found by testing, not review: Supabase's default ACL still hands `anon` TRUNCATE/REFERENCES/TRIGGER/MAINTAIN even with Data-API auto-exposure off — `anon` truncated three tables cascade before it was revoked.** **Second, worse defect found only after pushing (migration `20260806222319_lock_down_grants.sql`): local and remote carry OPPOSITE default ACLs** — local `anon=Dxtm`, remote G_Demo `anon=arwd` — so a migration that only *adds* grants produced a locked-down local DB and a wide-open remote one (`anon` held INSERT/UPDATE/DELETE on all 7 tables incl. `service_embeddings`). RLS still denied every operation, so nothing was exploitable, but **verifying security locally proved nothing about the remote**. Fixed by stating the end state absolutely — `revoke all` then grant back — plus `alter default privileges revoke all`, so it lands identically on any target. Verified over REST with the browser key: embeddings 401, DELETE/POST on `deals` 401, forged seed row 401, legitimate `demand_events` write reaches the FK check. Next: 4.3 (75 hand-written descriptions) → offline embeddings → 4.2 sweep |
| 6.0 | Consolidate everything into one deployed page per `006-one-page/{BRIEF,SPEC}.md` | 🟡 | **BRIEF + SPEC written 2026-08-06, awaiting approval.** SPEC §3.1 is the screen-by-screen product (S1–S7) and the four cut proposals with their evidence — read it first if the question is "what are we building". Reverses three approved decisions (004 E1 "beside not part of"; SPEC §1 "make it look like Groupon — CUT"; new scope: a grounded data agent). Build order is unchanged — SPEC §10, and **step 4 still gates all UI**. Live-data positioning settled inside it |
| 4.2 | Threshold sweep vs Part A's labelled pairs; report error rate | ⬜ | SPEC §6. Gates all UI work |
| 4.3 | Hand-write the 75 deal descriptions | 🟡 | **Drafted 2026-08-07, awaiting line-by-line review.** `supabase/service_descriptions.yaml` — each in its **own market's language** (English in every doc would make FINDINGS §5b's language test unmeasurable); `gloss_en` is review-only and never embedded. **D2 is now a test, not a discipline:** `check_descriptions.py` derives forbidden tokens from `classify.py`'s CONCEPTS — the 5 ABSENT concepts *and* the 4 PLAUSIBLE ones (naming yoga/pilates/crossfit would silently promote a judgement call to a fact) — and `build_seed.py` **aborts** if it fails. Mutation-tested: the first version missed `Fallschirmspringen` because it anchored both word ends; stems need a **left boundary only**. `doc` = title · l1 · l2 · description, no city/market token (D-A) |
| 4.4 | Host it — link preferred over zip | 🟡 | **DB half done 2026-08-06.** Linked to project `ewknlggenhrlftdukwme` (**G_Demo**, eu-central-1) — verified empty before the first push. Two migrations applied; **schema only, no seed** (`db push` does not seed, and `seed.sql` opens with a TRUNCATE that is destructive against a live instance). Seed the remote after step 4 settles the schema. `web/app/.env.local` still points at localhost — deliberate, local dev stays local. Left: FE hosting on Vercel |
| 5.1 | Two pages against their four bullets | ⬜ | |
| 5.2 | Measurement: dead-end rate (52.5%) replaces zero-result rate (29.3%) | ⬜ | **Verify first** — see known issue #3 |
| 5.3 | Platform asks in priority order | ⬜ | (1) query→results mapping + relevance label; (2) make the discriminating term constrain, audit expansion; (3) fix `SuggestedSearchQueries` |
| 5.4 | "What would tell you it is *not* working" | ⬜ | Where most writeups go thin |
| 5.6 | The log: hours, AI tools, what they got wrong | ⬜ | Use the adrenaline misclassification, not a generic line |
| ~~7.1~~ | ~~Live validation P1–P6~~ | ✅ | **CLOSED 2026-08-06** — ran ~option 3 (GB + PL, C2-guarded). P3 & P4 **confirmed**, P1 **falsified into something stronger**, P2 replicates but does not generalise, P5 falsified helpfully, P6 replicated cross-host. `003-live-validation/RESULT.md` |
| ~~7.2~~ | ~~Propagate the P1–P6 results~~ | ✅ | **CLOSED 2026-08-06.** F5 → 0 in `002-recoverability/notebook.py` (59 → **36**/mo; 17.9% → **11.8%**); `FINDINGS.md` §1 + new §5e; INDEX Now/Next. Every live finding tagged live-catalogue-only |
| ~~7.3~~ | ~~Amend `001-part-b/SPEC.md` §3/§4 from the live results **and from §5f**~~ | ✅ | **CLOSED 2026-08-06.** F3 relabelled *Uneven across cities*, diagnosis withdrawn, cross-city now gated on `dead_another_city > 0` rather than on the class; population and the 25% range kept deliberately. F5 recast as an unexplained residual, its 1–2-result behaviour re-grounded on the §1 cliff. Demo query moved off `crossfit` (FR) — all 27 of its dead ends are can't-tell, so it could never demo a location claim — onto `manicura` (ES), all 21 same-city. Four-bucket vocabulary added with the band. Old note: F1 better justified (fragment matching, "no lever"). **F5's row: its 40% is withdrawn.** **F3's row is worse — its whole "20 in Kraków, 90 minutes away" behaviour is built on a diagnosis that is false for 315 of 321 rows** (known issue #12). Also add the bucket vocabulary: the prototype should say *where the answer was*, which is what the analysis now leads with |
| 7.4 | Finish the unrun live scope if it ever matters | ⚪ | DE/FR/ES hosts, 18 non-capital divisions, P5 row 5.5 (% beyond 20 km). Parked — no current claim depends on them. `003-live-validation/RESULT.md` §"Scope actually run" |
| ~~8.1~~ | ~~Build `004-data-story`~~ | ✅ | **CLOSED 2026-08-06.** `outputs/explainer.html` (256 KB, self-contained, no kernel) + `outputs/notebook.html`. Verified in-browser. `004-data-story/RESULT.md` |
| 8.2 | Host `explainer.html` (folds into 4.4) | ⬜ | Currently a local file. A link beats a zip for a grader |
| 6.2 | Notebook: demand–supply divergence per market | ⬜ | **Jensen–Shannon, not KL** (KL → ∞ on zero-stock concepts). Supply from deal **titles**, not `category_l2` |
| 6.4 | Move the top-50 concentration stat into `FINDINGS.md` | ⬜ | Top 50 queries = 64.5% of searches; top 50 zero-queries = **80.3% of all zeros**. Currently lives only in `README.md` |
| 6.5 | Pressure-test the F1/F3/F5 recoverability assumptions | ⬜ | Only F2 has a measured anchor. The notebook states ranges; Part C must not quote the midpoint alone |
| ~~6.6~~ | ~~The right-hand tail: searches returning 26+ results convert at 2.3% vs 17.8%~~ | ✅ | **CLOSED 2026-08-06 — tested and rejected. A generation artifact; the dead-end definition does NOT widen, 52.5% stands.** Which searches land above 25 is flat across market (6.8–8.2%), city (4.5–10.0%), coverage (6.5–8.1%) and language (7.3% vs 8.3%) — indistinguishable from a shared random draw (χ² p=0.65). Landing in **1–2 is** query-predicted (p=4×10⁻¹⁶), which is what *validates* the ≤2 rule. Decisive: across **123 market+query pairs seen in both bands**, the same query converts **18.3%** at 4–25 and **2.6%** at 26+ (106/123 lower, p=6×10⁻²³). **Two claims in the original row were withdrawn** — the 'concepts stocked nowhere' concentration (an artifact of not grouping by market; coverage mix is identical to 4–25) and 'F1 signature'. `FINDINGS.md` §0, §8, §9 row 13 |

**Closed since the last reconcile:** 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 5.5 (upper bound
recomputed to **299** at 11.36% s2p). Parked: 1.4, 1.5 — low value against an empty Part B.

## Known issues

| # | What is wrong | Where | Risk if not fixed |
|---|---|---|---|
| 1 | **Two independent hand-built `CONCEPTS` maps that disagree.** `classify.py` puts 1,576 searches under `adrenaline`, all zeros — 59.9% of all zeros. `FINDINGS.md` quotes **47.6%** from `validate.py`'s narrower map | `validate.py`, `classify.py` | Two defensible numbers for one claim. **Do not put an adrenaline share in Part B UI copy or Part C until reconciled** — quote per-cell counts, which are directly computed |
| 2 | `validate.py`'s `unmapped` bucket is still 3,806 searches / 883 zeros | `validate.py` `CONCEPTS` | Understates adrenaline. This is the *cause* of #1 |
| ~~3~~ | ~~The 52.5% cliff has not been checked for concept-mix composition~~ | ~~`FINDINGS.md` §1~~ | **CLOSED 2026-08-06.** Stratified on concept × city: s2p 1.68% → 1.70%, direction holds in 137/138 strata. The cliff is result count, not mix. 5.2 unblocked |
| 4 | ~~no search returns exactly 3~~ **RESOLVED 2026-08-06 — generation artifact** (live returns 3 routinely; `RESULT.md` P4). Still open: paintball's healthy conversion could be substitution or generator artifact | `FINDINGS.md` §1, §5e | Halved. The live substitution mechanism (§5e) makes "substitution" the likelier reading but is **not** evidence about this dataset. Item 1.6 owns the remaining half |
| 6 | **Two rules, two counts, for the supply void.** `validate.py`: `zero_rate == 1.0` → **185 pairs / 1,691 searches / 64.2% of zeros** (what `FINDINGS.md` and Part C quote). `classify.py`: `coverage == 'absent' AND zero_rate >= 0.5` → **178 / 1,689** (what `query_classes.csv` and the prototype use). 170 pairs in both; the 21 always-zero-not-F4 are n=1 typos against stocked concepts, correctly excluded | `validate.py` L2, `classify.py` `classify()` | Part C and the prototype quote different numbers for the same finding. **Not an error — a definition.** Decide which Part C leads with and say why. Same shape as the 11.4/11.5 drift just closed |
| 7 | The two files also disagree on the **pair universe** — 185 vs 191 pairs at `zero_rate == 1.0` | `validate.py` vs `outputs/query_classes.csv` | Six pairs unaccounted for. Small, but it is the denominator under #6 |
| 8 | `classify.py`'s concept map misfires on typos: `paaracaidismo` → `massage`, `skyiving`/`shaark diving` → `dining_generic` | `classify.py` `CONCEPTS` | All affected rows are n=1 so no headline moves, but the Part B staff panel displays the concept and would show a visibly wrong one |
| 9 | **`division` typos fail silently — no error, just a wrong number.** An invalid division falls back to a default scope and `browseProps.division` echoes what you *sent*. `.fr`: `paris` → 444, `not-a-division` → 399, `zzzzqqq` → 399. Fallback differs per host (GB 431, FR 399) | live probe / any live claim | Every cross-market live comparison is confounded and looks fine. Run `divisionControl()` per host first. Actually verified: **`london`, `paris` only**. `berlin`/`warszawa` observed but control never run; `madrid` unprobed |
| 10 | **`offset` is silently ignored** unless `feedToken` is echoed with `isFetchMore:true`. `offset:400` returns page 1 | `live_probe.js` | Any deep-paging probe measures page 1 repeatedly. Fixed in v2 (`pageAll()`), but any earlier hand-run paging is suspect |
| 11 | **Live GB stocks paintball (12) and sushi (28)** — the dataset says both are stocked nowhere | `FINDINGS.md` §3, Part C | F1's headline examples describe the **synthetic catalogue only**. Part C must not imply Groupon lacks paintball. Also invalidates the obvious live inert-token probes — see `QUERIES.md` P1 row 1.0 |
| 13 | **`STOCK_TITLE`'s `gym` regex is cross-market asymmetric.** GB's *"Unlimited Fitness Classes"* matches on `fitness`; the four local-language equivalents — *Unbegrenzte Kurse* (DE), *Clases Ilimitadas* (ES), *Cours Illimités* (FR), *Zajęcia bez Limitu* (PL) — match nothing | `classify.py` `STOCK_TITLE`, found 2026-08-06 while seeding `service_concepts` | **Immaterial to every published number, checked not assumed:** every market has a separate gym title that matches, so `coverage` stays `stocked` in all five, and city coverage for `gym` is **identical** with or without the *Unlimited* titles — no `inventory_location` bucket moves. It only inflates GB's `deals_stocking` (24 vs 11). **Not fixed** — INDEX says no more Part A hardening, and a fix would churn numbers for no gain. **Worth one line in Part C:** the analysis's own concept map has a language gap, which is the same class of defect it diagnoses in Groupon's search |
| 12 | **`F3_geographic` measures city-to-city *variance*, not location.** Only **6 of its 321** dead ends have the answering deal in another city; 158 are same-city, 157 can't-tell. Diagnosis withdrawn 2026-08-06, population and 25% range retained | `classify.py` `classify()` L208, `FINDINGS.md` §5d/§5f | **Live exposure, not a footnote:** F3 contributes 12.9 of the 36.3 purchases — 36% of the whole search-side estimate. Tightened figures (7.8%, 5.7%) are published alongside. Shipped UI copy *"just not in your city"* was false for 315 of 321 rows — **fixed** in `004/notebook.py` `BEHAVIOUR`, but `001-part-b/SPEC.md` §3/§4 still carries it (item 7.3) |
| 13 | **The `plausible` coverage tier moves the Chapter 3 headline by 21.5pp.** All 1,016 of its dead ends land in one bucket together, and under `stocked_generic` same-city (2,306) overtakes nowhere (2,211) — the ordering flips | `classify.py` `PLAUSIBLE_COUNTS_AS`, `outputs/inventory_sensitivity.csv` | **Not an error — a judgement, now testable.** Lifted to a named constant so all three readings re-run. **Never quote one end of [43.2%, 64.7%] alone**; the explainer prints the whole band and names the flip |
| 14 | **`validate.py`'s typo nearest-neighbour is non-deterministic.** It ties-breaks off `set` iteration order, so the answer depends on `PYTHONHASHSEED`: `puintball` → `paintball` *or* `peintball`, `maniküe` → `maniküre` *or* `maniküue`, `go karuing` → `go karting` *or* `go karoing` — identical similarity, different pick per run. Found 2026-08-06 by diffing two runs of the unchanged script | `validate.py` Layer 4 | **No count moves, so no headline is affected** — but the repo's rule is "re-run the script before quoting any number", and this table's *examples* change between runs. Sort candidates before taking the max, or quote counts only, never a named nearest match |
