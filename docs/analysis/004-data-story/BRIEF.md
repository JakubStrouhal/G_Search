---
created: 2026-08-06
updated: 2026-08-06
note: Opens the data-story unit — asks for a business-readable presentation layer over Part A whose explainer hand-types no numbers.
---

# 004 — The data story: a business-readable answer to "why doesn't it work?"

Opened 2026-08-06. **Awaiting approval — nothing built yet.**

## What this is

Part A currently exists as three Python scripts, a 407-line `FINDINGS.md` and a notebook whose
stated jobs are *validate* and *simulate*. All of it is correct and none of it is readable by the
audience that decides. This unit produces the **presentation layer**: the same numbers, arranged as
an argument, with the mechanism made concrete enough to be checked.

Two artifacts, one source of truth:

| Artifact | Audience | Contains |
|---|---|---|
| `notebook.py` → `.ipynb` → `outputs/notebook.html` | someone checking the working | every number, recomputed from the CSVs, with the code visible |
| `outputs/explainer.html` | a grader who clicks a link | the narrative, the request-lifecycle drill-down, the query simulator |

**The explainer hand-types no numbers.** The notebook emits `outputs/story_data.json`; the build
step inlines it into the HTML. A number that changes in the data changes on the page.

## Decisions taken in the 2026-08-06 interview

| # | Question | Decision | Consequence |
|---|---|---|---|
| **E1** | Relationship to Part B | **Beside it, not part of it.** | Part B still needs its own build per `001-part-b/SPEC.md` §10. The hours are additive and must be logged as such. This unit does **not** reduce Part B's remaining work. |
| **E2** | How it is consumed | **Both** — notebook for the working, static HTML for the grader. | Interactivity must survive `nbconvert`. That rules out `ipywidgets`, whose callbacks need a live kernel. The explainer is plain inline JS over precomputed JSON. |
| **E3** | Simulator scope | **Replay the real queries only.** | Lookup against `query_classes.csv`, not embeddings. Traceable to Part A by construction; consistent with SPEC §2 (the class comes from the CSV, not from a threshold). A query not in the log says so honestly — that is itself in character. **No embedding work in this unit.** |
| **E4** | Live vs supplied data | **Both, visibly separated.** | Every live observation pinned with market · city · query · date. Two distinct visual treatments so no reader can merge them. `FINDINGS.md` §5e opens with the catalogue-conflation trap. |
| **E5** | Live probe | **Run P1–P5 first, via browser automation, read-only.** | ~45 min before the build. P4 can move a number in `002-recoverability`. See "Dependency" below. |
| **E6** | Contested numbers | **Route around them.** | No adrenaline share (47.6% vs 59.9%, known issue #1). No supply-void aggregate pair count (185/1,691 vs 178/1,689, #6). No pair-universe figure (185 vs 191, #7). **Per-cell counts only** — GB helicopter tour 100/100/0 — which are identical under both rules and directly computed. |
| **E7** | Technical depth | **Concrete request lifecycle.** | Real GraphQL request → what the ranker does with the tokens → the JSON that returns → what is absent from it. Anchored on captured payloads, expandable per stage. Not a search-engine tutorial. |
| **E8** | Size | **4–5 chapters, ~4 h.** | Output-per-hour is graded and Part B is at zero lines. Chapters that do not carry the argument are cut, not deferred. |

## The narrative spine

The brief asks *what is broken*. The answer is an arc, and the arc is the finding:

1. **The number you would report is the wrong number.** 29.3% zero-result is what any dashboard
   shows. 1–2 results converts like zero (s2p 1.7% vs 16.1%), so the real dead-end rate is **52.5%**
   — and that cliff survives concept × city stratification, so it is a property of result count, not
   of which queries land there.
2. **Why it doesn't work — what actually happens when you search.** The request lifecycle, made
   concrete. The load-bearing observation: a token the catalogue has never heard of is *exactly
   inert*. `xqzjw massage` returns the same count as `massage`. Nothing you type constrains the
   results, so the system can never tell you it had nothing — it always has something.
3. **Three structurally different failures, not one.** Volume by class. The one that matters most is
   invisible to every zero-result metric: a full page of results that do not answer the question.
4. **Most of this is not a search problem.** The recoverability split. Central estimate **11.8%**,
   range 5.6–15.1% — even at the optimistic end, search work is ~15% of the recoverable opportunity;
   the rest is inventory that does not exist. That part is assumption-free — F4 is zero by
   construction, not by estimate. *(Was ~18% before live probe P4 killed F5's basis on 2026-08-06.)*
5. **Try it yourself.** Type any of the 613 real queries and see the class, the real counts, and
   what the system does with it.

Chapter 2 is the one that answers "why," and it is the chapter that does not currently exist
anywhere in the repo.

## Dependency — live validation runs first

`003-live-validation/BRIEF.md` P1–P6 are pre-registered and pending (queue 7.1). Chapter 2 rests on
live evidence that is currently **one query pair**. Before the build:

- **P1** — does a real-but-unstocked word behave like gibberish? (`paintball massage` vs `massage`)
- **P2** — does the multi-token diacritic penalty replicate?
- **P3** — does live Groupon stock adrenaline in these cities? *(Likely yes. Constrains what Part C
  may claim; run it anyway — a limit we find is honesty, the same limit a grader finds is a hole.)*
- **P4** — does live ever return exactly 3? **`live_probe.js`'s own header already records `masaz`
  in division `warsaw` returning 3.** If that replicates, the supplied data's 0,1,2,→4 gap is a
  generator artifact, F5's 40% recoverability assumption loses its basis, and the notebook's central
  estimate falls from ~59 to ~36 purchases/month. **This rewrites a number before it gets presented.**
- **P5** — does live widen radius with distance framing?

Constraints carried from that brief: read-only, exact integer counts (never the UI's buckets),
every observation pinned, human pacing.

## Deliverables

```
docs/analysis/004-data-story/
  BRIEF.md                    this file
  notebook.py                 jupytext source of truth; emits story_data.json
  build_explainer.py          inlines the JSON into the HTML template
  explainer.template.html     the page, no numbers in it
  outputs/notebook.html       executed export
  outputs/explainer.html      self-contained, no network, no kernel
  outputs/story_data.json     the contract between the two
  RESULT.md                   what was found, what moved, hours
```

Also updated, if the live probe changes an input: `002-recoverability/notebook.py`,
`FINDINGS.md` (tagged for which catalogue), `INDEX.md`.

## Out of scope — stated, not deferred

- **Embeddings, semantic matching, threshold sweeps.** That is Part B, SPEC §10 steps 2–4.
- **Reconciling the two `CONCEPTS` maps.** More Part A hardening; INDEX says don't. Routed around
  per E6.
- **Visual design.** Explicitly not graded. Legible beats attractive.
- **Making this the Part B prototype.** It is not one, and claiming it were would fail the brief's
  honesty criterion. The explainer will say so in a line.

## Done looks like

1. P1–P5 marked confirmed / falsified / inconclusive with exact pinned counts.
2. Any number the probe moved is corrected **at the source** — the notebook, not the prose.
3. `explainer.html` opens from a file with no network and no kernel; the simulator works; every
   number in it traces to `story_data.json`.
4. Live and supplied observations are impossible to confuse on the page.
5. No contested number appears anywhere in it.
6. Real hours logged for Part C's tools-and-hours log.
