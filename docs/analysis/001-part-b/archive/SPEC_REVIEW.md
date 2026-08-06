# Part B build spec — review

Written 2026-08-05, against `BUILD_SPEC.md` (same folder), checked against
`PLAN.md`, `docs/analysis/FINDINGS.md`, `README.md` and `CLAUDE.md`.

**Verdict.** The spec is strong on *what to prove* and weak on *whether the
build will actually prove it*. The thesis ("not a search-quality problem, a
marketplace liquidity problem that search is measuring"), the staff panel, and
the CUT list are the best things in it and should survive untouched. Four
issues would break the demo or the grade; one of them is load-bearing for the
entire demo script.

---

## Decisions to make before building

Tick these off tomorrow. Each is expanded below.

- [ ] **D1** — Verify the threshold actually separates paintball from
      skydiving. If it doesn't, tier assignment moves to `query_classes.csv`.
      *(Do this first — it can invalidate the demo script.)*
- [ ] **D2** — LLM-enriched deal descriptions: drop, or hand-write 75?
- [ ] **D3** — Stack: Supabase + Vercel, or static bundle with precomputed
      vectors?
- [ ] **D4** — Seed the demand table from `search_log.csv` (yes — this one is
      a bug fix, not really a choice).
- [ ] **D5** — Demo query #2: keep the designed `masaż`-in-London scenario, or
      swap it for the 1–2 result cliff?
- [ ] **D6** — Write the coverage table (F1–F6 × tiers → behaviour → demo
      query → or "cut, and why").

---

## Blocking

### 1. Nothing guarantees the thresholds produce the demo script

The biggest hole. The spec distinguishes Tier 1 (paintball) from Tier 2
(skydiving) by **catalogue truth**, but at runtime it separates them with a
single similarity threshold. Both have zero matching inventory. Against a
catalogue of city tours, escape rooms, karting, fitness, beauty, dining and
massage, there is no principled reason paintball scores above `LOW` and
skydiving below it — karting may sit closer to skydiving's thrill vector than
to paintball's, and the ordering could invert.

Demo queries #3 and #4 both depend on that separation holding, and it is
unverified. Build-order step 3 half-anticipates this ("get the three bands
right before touching the UI") but does not treat it as a possible dead end.

**Do this before any UI work:** embed the 75 unique titles, embed `paintball`
and `fallschirmspringen`, print the cosine scores. Thirty minutes. If the
ordering doesn't hold, the fallback is issue 4 below.

### 2. The LLM-enriched deal description is a fabrication risk that attacks the central claim

`CLAUDE.md:90` records why the concept map was hand-built: an LLM-generated one
"is a fabrication risk that cannot be defended in Part C." §3 of the spec
proposes the same thing one layer deeper, and the failure mode is specific:

> If enrichment writes "outdoor adventure, adrenaline, thrills" onto the 132
> `activities` deals, skydiving clears `LOW`, **Tier 2 collapses into Tier 1,
> and the demo's central finding becomes an artifact of generated text.**

There are only **75 unique titles**. Hand-write 75 descriptions — cheaper than
building and auditing an enrichment pass, and defensible line by line in Part
C. Commit the file, and show the matched document in the staff panel.

### 3. The stack is roughly a 3× time overrun on the graded axis

`PLAN.md` Phase 4 budgets **3–5 h**. Supabase + Vercel + pgvector + an offline
embedding pipeline + four screens + staff panel + brief view is realistically a
15–20 h build. Output-per-hour is graded and more hours is explicitly *not* a
better score (`CLAUDE.md:19`).

§6's own restraint argument, applied one level up, kills the stack: for a
read-only demo over 568 rows you don't need Postgres either. Precompute vectors
for the **75 unique titles per market**, ship a static bundle, deploy anywhere.
No backend, no keys, no DB, instant load. §6's "named restraint reads as senior
judgment" line still works in Part C — it just gets made about a smaller
system, which is the stronger version of the same argument.

The only write path is the demand table, and it is simulated anyway —
`localStorage` over a seeded baseline covers it (see next).

### 4. §4's demand table has no data source, and the Part A→B contract is already built

**The bug.** "47 people searched this in Berlin last month" is unwired. The §4
diagram builds the table from runtime abstention events, so a fresh demo shows
"1 search." That number must be **seeded from `search_log.csv`**, where it
already exists and is real: GB helicopter tour 100 searches, GB skydiving 91,
DE fallschirmspringen 64. Grader clicks then increment a real baseline. Seeding
is also the more honest artifact.

**The bigger point.** `PLAN.md` Phase 2.3 makes `query_classes.csv` "the
contract between Part A and Part B — the prototype reads it, so the connection
between analysis and build is mechanical rather than asserted." That directly
answers the grading criterion *"whether the prototype reflects the analysis
rather than being a nice search UI bolted on beside it."* The spec derives
tiers from live thresholds instead and never reconciles the two.

**And the artifact already exists.** `docs/analysis/outputs/query_classes.csv`
— 751 market+query rows, with `failure_class` (`F4_supply_void`, …), `concept`,
`searches`, `zeros`, `deads`, `city_spread`, `coverage`, `deals_stocking`,
`is_english`. So this is not new work; it is a `fetch()`. Wire it in:

- **`query_classes.csv` assigns the tier.** Deterministic, traceable to Part A,
  and immune to issue 1.
- **Thresholds set presentation confidence within the tier.** Still the
  interesting product mechanic, still worth demoing, no longer load-bearing for
  the demo script.
- **Staff panel shows both**, so a grader sees agreement — or disagreement,
  which is honest and more interesting than either alone.

---

## Add: a coverage table

The brief's hard requirement is "every query type found in Part A, **including
the ones you cannot fix**." Nothing in the spec demonstrates that completeness.
One table, as a required deliverable:

| Part A class | Prototype behaviour | Demo query | or: cut, and why |
|---|---|---|---|

Cover both `PLAN.md`'s **F1–F6** and the three tiers — `CLAUDE.md:32` says the
prototype's behaviours are keyed to the F-classes, and the spec works only in
tiers. F6 (goods vs experiences) is live-only and defensibly cut, but must be
*stated* as cut, not silently absent. A grader checks this in ten seconds.

Two gaps the table exposes immediately:

- **The headline finding has no demo slot.** 52.5% dead-end / "1–2 results
  converts like zero" is the single most important number in Part A. Tier 3's
  spec mentions treating 1–2 as near-empty, but no demo query exercises it. It
  should be demo #2 — replacing `masaż` in GB/London, which costs a fabricated
  scenario in a five-query script where honesty is graded, and only re-makes
  demo #1's point.
- **§2 item 4 rules out geographic widening on the wrong grounds.** "Not
  possible in this dataset — no aerial anywhere" is true of *aerial* only. F3
  is demoable for real on intermittent concepts: ES crossfit runs 0% in one
  city and 43.8% in another; median city spread 0.199. A demoable behaviour was
  cut by mistake.

---

## Two upgrades that are nearly free

### Cite the live recon in Tier 1

As written, Tier 1 rests on the corpus's **weakest** evidence — `FINDINGS.md`
§3, explicitly tagged CANNOT VERIFY ("paintball returns escape rooms" is
inferred from category structure). Meanwhile exact, replayed, production-
**observed** proof of the same mechanism sits unused in `PLAN.md` §4:

> `xqzjw massage` = `massage` = **458**. Identical. Two markets, five category
> heads. `xqzjw` alone returns 0.

Put 458 = 458 on the Tier 1 screen and in the staff panel. One line, and it
moves the riskiest claim in the build from inference to observation.

### The calibration set already exists — use it

Hand-tuning two scalars against two anchor cases is fitting, not calibration,
and Part C then has to confess it. But Part A emits **185 always-zero pairs**
and the never-zero set — a few hundred labelled pairs for free, already in
`query_classes.csv`. Sweep `HIGH`/`LOW` against them and report the error rate.

"Thresholds calibrated against N labelled pairs from Part A, X% disagreement,
here are the failures" is *evidence* rather than a confession — and it doubles
as the verification for blocking issue 1.

**Also worth adding to the staff panel:** *what today's system would have
shown* (a full page of N results) beside what this shows. That side-by-side is
the most persuasive single artifact for the Tier 1 claim and costs almost
nothing.

---

## Minor

- **Cut the two personas.** A UI control that changes only copy, requiring a
  Part C caveat, in an exercise where honesty is graded — cost exceeds benefit.
- **Build-order step 9 ("make it look like Groupon")** — visual design is
  explicitly not assessed. Cut it, don't defer it.
- **§9's Layer 3 fix is a build input, not a "before quoting" item.** The
  demand table aggregates by concept, so it inherits the concept map. It is a
  dependency of build step 5.
- **s2p is 11.4%, not 11.5%** (`CLAUDE.md:111` — `FINDINGS.md` §5 has drifted).
  Re-run `validate.py` before the acquisition-brief view quotes it. Same for
  47.6% adrenaline, which §9 correctly notes will *rise* once `unmapped` is
  fixed — don't hard-code it in UI copy.
- **Everything else checks out** against `FINDINGS.md`: 64.2% / 35.8%, 185 /
  179 pairs, 1,691 / 942 searches, median 7–9 results, 12–25% intermittent
  rates, spread 0.199, 1.7% s2p at 1–2 results, zero paintball/crossfit/sushi/
  bowling deals.

---

## What to keep exactly as written

- The one-sentence thesis.
- The staff panel as the spine of the demo (§5) — the highest-value component
  in the spec, and the literal answer to "show your working".
- Both CUT decisions (returning-customer recs, real vendor-outreach agent) and
  the reasons given.
- The abstention framing: *"knowing when to return nothing is the product
  requirement, not an edge case."*
- The nth-order observation in Tier 1 — that loosening matching to cut
  zero-results makes the invisible failure *worse*, dashboard green while trust
  falls. That is the single sharpest paragraph in the document.
- The honesty register (§8), plus the additions flagged above.
