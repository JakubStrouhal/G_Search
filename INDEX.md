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
  (2026-08-06) around one question — *when a search failed, where was the answer?* The deliverable is
  `004-data-story/outputs/explainer.html`, now 5 chapters. Part B has an approved spec
  (`001-part-b/SPEC.md`) and a **stack-init unit in flight** (`005-stack-init/`, opened by a parallel
  session): `supabase/config.toml` and a local stack exist, **zero migrations and zero tables so
  far**. Part C not started. **B and C are still the whole remaining risk.**
- **The spine, and it is what Part C should open with.** Over all 4,720 dead ends:
  **nowhere in the market 43.2% · the user's own city 32.2% · another city 3.1% · can't tell 21.5%**.
  Four buckets, four owners; F1–F6 nests inside (`nowhere` **is** F1 ∪ F4, asserted in code).
  **Quote the `nowhere` band [43.2%, 64.7%], never one end** — the `plausible` seam moves 1,016 dead
  ends together and flips the ordering under one reading. Beats a shuffled null under every reading
  (+9.8pp to +14.0pp, z 19.5–33.6, seed 7). `FINDINGS.md` §5f.
- **Top next actions (ranked):**
  1. **Build Part B** from `001-part-b/SPEC.md` — §6 architecture, §10 build order. Step 1 is
     Supabase migrations + seeds; **step 4 (threshold sweep) gates all UI work**. Budget tension is
     real and stated in §6: log the real hours. **Do 7.3 first** — the SPEC's F5 row still asserts a
     ranking cutoff the live probe killed, **and its F3 row now needs the same treatment**.
  2. **Part C.** Draft after B exists. Open with the bucket split, then the language test; the 52.5%
     is support, not the headline. Three ready-made "what the AI tools got wrong" examples: the
     adrenaline→`activities` misclassification, the P3 multi-word supply misread corrected the same
     day, and F3's "geographic" diagnosis surviving into shipped UI copy until it was tested.
  3. Remaining notebook angles: demand–supply divergence (6.2), top-50 stat into FINDINGS (6.4).
- **Two things Part C must carry.** The **language test** — English phrasing dead-ends 81.2% vs
  39.0% local, a controlled 42.3pp gap across 47 of 48 matched pairs, with both confounds killed.
  And the **recoverability split** — search work is only **~12%** of the recoverable opportunity
  (central 11.8%, range 5.6–15.1%), **+36 purchases/mo against 723 today = +5.0%**, versus a
  supply-void ceiling of +271 (+37.5%). **The old ~18% / 59-purchases figures are dead.** Every way
  of tightening the search side lowers it (7.8%, then 5.7%) — publish the most generous and say the
  others exist.
- **Deliberately not doing:** any more Part A hardening. B is still empty.
<!-- state:end -->

## Decisions — last 6, newest first, oldest row deleted on write

<!-- decisions:start -->
| Date | Decision | Why |
|---|---|---|
| 2026-08-06 | **Explainer re-spined on "where was the answer?"; F1–F6 nests inside** | Six classes is more than a reader holds, and *where* assigns an owner where *why* does not |
| 2026-08-06 | **F3's "geographic" diagnosis withdrawn, range kept at 25%** | 6 of 321 dead ends are really another-city. Re-deriving lowers the headline; publish the generous one |
| 2026-08-06 | Stack: **imperative migrations, local-only, publishable key** — not declarative, not linked | Budget; nothing before hosting needs a remote. Anon keys are compatibility-only per Supabase |
| 2026-08-06 | **F5 recoverability withdrawn; the split is ~12%, not ~18%** | Live P4: Groupon returns exactly 3 routinely, so the ranking-cutoff inference is dead |
| 2026-08-06 | 004 data-story: beside Part B, replay-only simulator, no embeddings | Part A has no readable artifact; embeddings would make it a second 15 h Part B build |
| 2026-08-06 | **Supabase + Vue3, DB–BE–FE — reverses D3's static bundle** | Owner's call: this is a software product, not a demo bundle. Budget tension noted in SPEC §6 |
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
| 4.0 | Stack init per `005-stack-init/BRIEF.md` | 🟡 | **Steps 1–4 and 6–9 done 2026-08-06.** Local stack boots with **zero migrations**; `web/app` (Vue3+Vite+TS) builds and its health check reads PostgREST 200 + a `PGRST205` round trip, verified in-browser. Step 5 (remote link) **deferred — local-only until hosting**. Left: **10** (the `.claude` supabase agent — partly superseded, Supabase's own skills are installed) and **11** (doc sweep, mostly done) |
| 4.1 | Build Part B per `001-part-b/SPEC.md` §10 | ⬜ | The entire remaining risk. Step 1 (schema + generated seeds) is the next real unit |
| 4.2 | Threshold sweep vs Part A's labelled pairs; report error rate | ⬜ | SPEC §6. Gates all UI work |
| 4.3 | Hand-write the 75 deal descriptions | ⬜ | SPEC §6 (D2) |
| 4.4 | Host it — link preferred over zip | ⬜ | |
| 5.1 | Two pages against their four bullets | ⬜ | |
| 5.2 | Measurement: dead-end rate (52.5%) replaces zero-result rate (29.3%) | ⬜ | **Verify first** — see known issue #3 |
| 5.3 | Platform asks in priority order | ⬜ | (1) query→results mapping + relevance label; (2) make the discriminating term constrain, audit expansion; (3) fix `SuggestedSearchQueries` |
| 5.4 | "What would tell you it is *not* working" | ⬜ | Where most writeups go thin |
| 5.6 | The log: hours, AI tools, what they got wrong | ⬜ | Use the adrenaline misclassification, not a generic line |
| ~~7.1~~ | ~~Live validation P1–P6~~ | ✅ | **CLOSED 2026-08-06** — ran ~option 3 (GB + PL, C2-guarded). P3 & P4 **confirmed**, P1 **falsified into something stronger**, P2 replicates but does not generalise, P5 falsified helpfully, P6 replicated cross-host. `003-live-validation/RESULT.md` |
| ~~7.2~~ | ~~Propagate the P1–P6 results~~ | ✅ | **CLOSED 2026-08-06.** F5 → 0 in `002-recoverability/notebook.py` (59 → **36**/mo; 17.9% → **11.8%**); `FINDINGS.md` §1 + new §5e; INDEX Now/Next. Every live finding tagged live-catalogue-only |
| 7.3 | Amend `001-part-b/SPEC.md` §3/§4 from the live results **and from §5f** | ⬜ | **Now the top pre-build task.** F1 better justified (fragment matching, "no lever"). **F5's row: its 40% is withdrawn.** **F3's row is worse — its whole "20 in Kraków, 90 minutes away" behaviour is built on a diagnosis that is false for 315 of 321 rows** (known issue #12). Also add the bucket vocabulary: the prototype should say *where the answer was*, which is what the analysis now leads with |
| 7.4 | Finish the unrun live scope if it ever matters | ⚪ | DE/FR/ES hosts, 18 non-capital divisions, P5 row 5.5 (% beyond 20 km). Parked — no current claim depends on them. `003-live-validation/RESULT.md` §"Scope actually run" |
| ~~8.1~~ | ~~Build `004-data-story`~~ | ✅ | **CLOSED 2026-08-06.** `outputs/explainer.html` (256 KB, self-contained, no kernel) + `outputs/notebook.html`. Verified in-browser. `004-data-story/RESULT.md` |
| 8.2 | Host `explainer.html` (folds into 4.4) | ⬜ | Currently a local file. A link beats a zip for a grader |
| 6.2 | Notebook: demand–supply divergence per market | ⬜ | **Jensen–Shannon, not KL** (KL → ∞ on zero-stock concepts). Supply from deal **titles**, not `category_l2` |
| 6.4 | Move the top-50 concentration stat into `FINDINGS.md` | ⬜ | Top 50 queries = 64.5% of searches; top 50 zero-queries = **80.3% of all zeros**. Currently lives only in `README.md` |
| 6.5 | Pressure-test the F1/F3/F5 recoverability assumptions | ⬜ | Only F2 has a measured anchor. The notebook states ranges; Part C must not quote the midpoint alone |

**Closed since the last reconcile:** 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 5.5 (upper bound
recomputed to **299** at 11.36% s2p). Parked: 1.4, 1.5 — low value against an empty Part B.

## Known issues

| # | What is wrong | Where | Risk if not fixed |
|---|---|---|---|
| 1 | **Two independent hand-built `CONCEPTS` maps that disagree.** `classify.py` puts 1,576 searches under `adrenaline`, all zeros — 59.9% of all zeros. `FINDINGS.md` quotes **47.6%** from `validate.py`'s narrower map | `validate.py`, `classify.py` | Two defensible numbers for one claim. **Do not put an adrenaline share in Part B UI copy or Part C until reconciled** — quote per-cell counts, which are directly computed |
| 2 | `validate.py`'s `unmapped` bucket is still 3,806 searches / 883 zeros | `validate.py` `CONCEPTS` | Understates adrenaline. This is the *cause* of #1 |
| ~~3~~ | ~~The 52.5% cliff has not been checked for concept-mix composition~~ | ~~`FINDINGS.md` §1~~ | **CLOSED 2026-08-06.** Stratified on concept × city: s2p 1.68% → 1.70%, direction holds in 137/138 strata. The cliff is result count, not mix. 5.2 unblocked |
| 4 | ~~no search returns exactly 3~~ **RESOLVED 2026-08-06 — generation artifact** (live returns 3 routinely; `RESULT.md` P4). Still open: paintball's healthy conversion could be substitution or generator artifact | `FINDINGS.md` §1, §5e | Halved. The live substitution mechanism (§5e) makes "substitution" the likelier reading but is **not** evidence about this dataset. Item 1.6 owns the remaining half |
| 5 | `docs/analysis/001-part-b/archive/` still holds the superseded draft spec and its review | `001-part-b/archive/` | Someone builds from the wrong file. Delete the folder after the first commit containing `SPEC.md` |
| 6 | **Two rules, two counts, for the supply void.** `validate.py`: `zero_rate == 1.0` → **185 pairs / 1,691 searches / 64.2% of zeros** (what `FINDINGS.md` and Part C quote). `classify.py`: `coverage == 'absent' AND zero_rate >= 0.5` → **178 / 1,689** (what `query_classes.csv` and the prototype use). 170 pairs in both; the 21 always-zero-not-F4 are n=1 typos against stocked concepts, correctly excluded | `validate.py` L2, `classify.py` `classify()` | Part C and the prototype quote different numbers for the same finding. **Not an error — a definition.** Decide which Part C leads with and say why. Same shape as the 11.4/11.5 drift just closed |
| 7 | The two files also disagree on the **pair universe** — 185 vs 191 pairs at `zero_rate == 1.0` | `validate.py` vs `outputs/query_classes.csv` | Six pairs unaccounted for. Small, but it is the denominator under #6 |
| 8 | `classify.py`'s concept map misfires on typos: `paaracaidismo` → `massage`, `skyiving`/`shaark diving` → `dining_generic` | `classify.py` `CONCEPTS` | All affected rows are n=1 so no headline moves, but the Part B staff panel displays the concept and would show a visibly wrong one |
| 9 | **`division` typos fail silently — no error, just a wrong number.** An invalid division falls back to a default scope and `browseProps.division` echoes what you *sent*. `.fr`: `paris` → 444, `not-a-division` → 399, `zzzzqqq` → 399. Fallback differs per host (GB 431, FR 399) | live probe / any live claim | Every cross-market live comparison is confounded and looks fine. Run `divisionControl()` per host first. Actually verified: **`london`, `paris` only**. `berlin`/`warszawa` observed but control never run; `madrid` unprobed |
| 10 | **`offset` is silently ignored** unless `feedToken` is echoed with `isFetchMore:true`. `offset:400` returns page 1 | `live_probe.js` | Any deep-paging probe measures page 1 repeatedly. Fixed in v2 (`pageAll()`), but any earlier hand-run paging is suspect |
| 11 | **Live GB stocks paintball (12) and sushi (28)** — the dataset says both are stocked nowhere | `FINDINGS.md` §3, Part C | F1's headline examples describe the **synthetic catalogue only**. Part C must not imply Groupon lacks paintball. Also invalidates the obvious live inert-token probes — see `QUERIES.md` P1 row 1.0 |
| 12 | **`F3_geographic` measures city-to-city *variance*, not location.** Only **6 of its 321** dead ends have the answering deal in another city; 158 are same-city, 157 can't-tell. Diagnosis withdrawn 2026-08-06, population and 25% range retained | `classify.py` `classify()` L208, `FINDINGS.md` §5d/§5f | **Live exposure, not a footnote:** F3 contributes 12.9 of the 36.3 purchases — 36% of the whole search-side estimate. Tightened figures (7.8%, 5.7%) are published alongside. Shipped UI copy *"just not in your city"* was false for 315 of 321 rows — **fixed** in `004/notebook.py` `BEHAVIOUR`, but `001-part-b/SPEC.md` §3/§4 still carries it (item 7.3) |
| 13 | **The `plausible` coverage tier moves the Chapter 3 headline by 21.5pp.** All 1,016 of its dead ends land in one bucket together, and under `stocked_generic` same-city (2,306) overtakes nowhere (2,211) — the ordering flips | `classify.py` `PLAUSIBLE_COUNTS_AS`, `outputs/inventory_sensitivity.csv` | **Not an error — a judgement, now testable.** Lifted to a named constant so all three readings re-run. **Never quote one end of [43.2%, 64.7%] alone**; the explainer prints the whole band and names the flip |
