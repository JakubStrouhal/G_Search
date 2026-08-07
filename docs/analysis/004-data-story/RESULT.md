---
created: 2026-08-06
updated: 2026-08-06
note: Records what the data-story unit built — the notebook, the templated explainer, and the JSON contract that keeps numbers out of the page source.
---

# 004 — result

Built 2026-08-06. Brief: `BRIEF.md`. Decisions E1–E8 were taken in an interview before any code.

## What exists

| Artifact | What it is |
|---|---|
| `notebook.py` | Source of truth. Recomputes every figure from the CSVs; emits `outputs/story_data.json`. Runs as a plain script or as a `# %%` notebook |
| `outputs/notebook.html` | Executed export — the working, with code visible |
| `explainer.template.html` | The page. **Contains no numbers**, only a `__STORY_DATA__` token |
| `build_explainer.py` | Inlines the JSON into the template; refuses to build if the page references anything external |
| `outputs/explainer.html` | **The deliverable.** 256 KB, self-contained, opens from `file://` with no network and no kernel |
| `outputs/story_data.json` | The contract between the two. 751 classified pairs + pinned live observations |

```bash
.venv/bin/python docs/analysis/004-data-story/notebook.py   # recompute + emit JSON
python3 docs/analysis/004-data-story/build_explainer.py     # inline JSON -> explainer.html
```

## The design decision that matters

**No number is hand-typed into the page.** The template carries a single token; the build step is the
only path data takes into the HTML. This exists because the repo's recurring defect is a stale figure
living inside a derived one — the 11.5 → 11.4 → 299 episode, and the ~18% → ~12% correction made
during this very unit. A page that hand-typed 18% would still say 18%.

The one exception is deliberate and labelled: the **pinned live observations** in chapter 2 are
observations, not computations, so they are transcribed into `notebook.py` with host · division ·
date attached.

## Verified, not assumed

Checked in-browser against the built file, not the template:

- No JavaScript errors; no leftover `__STORY_DATA__`; no mojibake (needed an explicit `charset`)
- No horizontal body scroll at 1495px; wide tables scroll inside their own container
- Theme toggle overrides the media query in **both** directions
- All six demo chips resolve, each to a **different** failure class, plus the unknown-query refusal
- `fallschirmspringen`/DE returns 64 searches / 64 zeros / 100% dead — matches `FINDINGS.md` exactly
- Chapter 4's split reproduces `002-recoverability` exactly: 36 purchases/mo, 11.8% central

## Two things that changed while building

**1. The simulator folds diacritics, and says so.** `masaz tajski` is not in the log; `masaż tajski`
is. Rather than fix the demo chip, the lookup now folds diacritics and displays a *normalisation
fired* panel naming the query it resolved to. This is the one fix the analysis claims genuinely
works, so the page performs it instead of describing it — and discloses it rather than resolving
silently, which is the behaviour the whole argument is about. It never invents a result: it resolves
to a real logged query and reports that query's real counts.

**2. Concept is shown with a confidence flag, not suppressed.** `SPEC.md` §9 offered "fix the map or
exclude `thin_n` rows from the panel" for known issue #8. Excluding would have blanked the concept on
**604 of 751** pairs — far more damage than the defect causes. Third option taken: show it, flag it
`low confidence, n≤3`. Disclosure beats both hiding and asserting.

## Contested numbers, excluded as briefed (E6)

Absent from the notebook and the page: the adrenaline share of zeros (47.6% vs 59.9%, known issue
#1), the supply-void aggregate pair count (185/1,691 vs 178/1,689, #6), the pair universe (185 vs
191, #7). Chapter 3 quotes **per-cell counts** instead — directly computed and identical under either
rule.

## Live vs supplied (E4)

Chapter 2 is a **fixed dark console in both themes**, opened by a violet banner stating that it is a
different catalogue and that nothing in it sizes anything in the supplied data. The device is not
decorative: the chapter looks like a terminal because it was captured from one.

## What this unit does NOT do

- **It is not Part B.** E1 was explicit: beside, not part of. `001-part-b/SPEC.md` §10 is untouched
  and `supabase/` and `web/` still do not exist. These hours are **additive**, and output-per-hour is
  graded — that tension is real and is recorded rather than smoothed.
- **No embeddings, no semantic matching, no threshold sweep.** The simulator is a lookup against
  `query_classes.csv` (E3). A query outside the log is refused, not modelled.
- **No visual design claims.** Explicitly ungraded; the page is legible, not decorated.

## Hours — **to be filled in by the owner**

`BRIEF.md` budgeted ~4 h and the brief requires an hours log as a deliverable. **The wall-clock
figure is the owner's to record, not the agent's** — an agent-side estimate would be a fabrication in
a log whose whole purpose is honesty about effort. What can be stated factually:

- Scope executed: interview (E1–E8) → live probe P1–P6 across 3 hosts → propagation of the two
  corrections → notebook → explainer → in-browser verification.
- These hours are **additive to Part B**, which is still at zero lines (E1).

| | Hours |
|---|---|
| 004 data story | *(owner to fill)* |
| of which live probe (003) | *(owner to fill)* |

## Open

| # | Item |
|---|---|
| 7.3 | `001-part-b/SPEC.md` §3/§4 still need amending from the live results — F5's row in particular still asserts a ranking cutoff that P4 killed |
| — | The explainer is a local file. Hosting it (pending 4.4) is a separate step |
| — | `INDEX.md` known issues #1, #2, #6, #7 remain open; this unit routed around them rather than closing them |
