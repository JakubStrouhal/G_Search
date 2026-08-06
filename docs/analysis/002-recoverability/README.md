---
created: 2026-08-06
updated: 2026-08-06
note: Frontmatter stamped mechanically — replace with one sentence on what changed and why.
---

# 002 — Recoverability · **what is it actually worth to fix this?**

Read this **second**, after `../004-data-story/`. This is where the money number comes from, and
it is the number an interviewer is most likely to push on.

## What you are looking at

A notebook that does two jobs, in this order:

1. **Validates the headline before anything is built on it.** The 52.5% dead-end figure rests on the
   claim that a search returning 1–2 results converts like a search returning zero. If that cliff
   were really *composition* — thin result sets skewing toward concepts that convert badly anyway —
   the headline shrinks and Part C's whole measurement proposal changes. Checked first, because
   everything downstream multiplies it.
2. **Simulates recovery per failure class.** Not "search is broken by X%" but "here is what fixing
   each class returns, and here is the assumption that number rests on."

| File | What it is | Show it to Groupon? |
|---|---|---|
| **`outputs/notebook.html`** | Executed export — narrative, code and output together. **This is the presentable artifact of this folder.** An nbconvert export, so it pulls MathJax/require.js from a CDN — fine hosted, degrades silently offline | **Yes — as the working behind the explainer's *sizing***: the +36/month, the 12%, the 271 ceiling. Chapter 4's charts are drawn in `../004-data-story/notebook.py`, not here |
| `notebook.py` | Source of truth. The `# %%` markers make it a notebook; it also runs as a plain script, and it is the version that diffs in git | Only if asked |
| `outputs/acquisition_priority.csv` | If you can sign N merchants, where — ranked | Yes, as a backup table |
| `outputs/data_vs_simulation.png` | The before/after chart | Yes |

## How to read it

Seven sections, and **section 1 gates the other six** — if the cliff had turned out to be
composition, nothing after it would mean anything.

| § | What it answers |
|---|---|
| 1 | Does the cliff survive stratification? *(the gate)* |
| 2 | The data — where the dead ends actually are |
| 3 | **Recoverability — the assumptions, stated** ← read this one slowly |
| 4 | The simulation |
| 5 | Sensitivity — how much does the answer depend on the guesses? |
| 6 | Allocation — if you can sign N merchants, where? |
| 7 | Chart — data vs simulation, side by side |

**The honesty rule the notebook is built on, and the thing to say out loud when presenting it:**
recoverability per class is an **assumption, not a measurement** — with one exception, F2 (language),
where the matched-pair language test gives a controlled anchor. Every assumption is named, given a
**range**, and its effect on the output is shown. A single point estimate presented as a forecast is
the exact failure mode the brief grades against.

## The outcome

| | per month |
|---|---|
| Purchases today, across five markets | **723** |
| Fixing every search-side class we can name | **+36 (+5.0%)** — about **12%** of the recoverable opportunity |
| The supply-void ceiling (merchant acquisition, not search) | **+271 (+37.5%)** |

**Search work is a minority of the prize, well behind the supply void.** That is the point of the
whole folder, and it is the same conclusion the bucket split reaches from a different direction.

## Cautions

- **`../FINDINGS.md` and the notebook own these numbers, not this page.** If anything here disagrees
  with `../FINDINGS.md` §5e or with a fresh run of `notebook.py`, **they win.** Re-run the script
  before quoting a figure out loud.
- **The old ~18% / 59-purchases-per-month figures are dead.** Withdrawn 2026-08-06 with F5's
  "ranking cutoff" — which rested on inferring a cutoff *from an absence* (no search returns exactly
  3) that **this data cannot attribute** between a cutoff and the generator. Unattributable, so
  withdrawn to zero rather than re-estimated. **The live probe corroborates the generator branch but
  is not the basis** — say it in that order, or you have imported a live-catalogue result into a
  supplied-data measurement. If you find 17.9% or 59 anywhere, it is stale; the current figures are
  **11.8%** and **+36/mo**. The exported `outputs/notebook.html` is post-correction and was checked.
- **Every way of tightening the search side lowers the estimate further** (11.8% → 7.8% → 5.7%). The
  published figure is the **most generous** one, and the fact that the others exist is stated rather
  than hidden. Say that before someone finds it.
- **Do not quote the midpoint of a range alone.** Only F2 has a measured anchor; F1, F3 and F5 rest
  on stated guesses. `INDEX.md` pending item 6.5.
- F3 and F5 kept their populations but **lost their names**. F5's "ranking cutoff" and F3's
  "geographic thinness" were both withdrawn as diagnoses; they are now residuals with no established
  cause, which is a *smaller* claim than the one they replaced. `../FINDINGS.md` §5d.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install pandas numpy scipy matplotlib jupytext jupyter
```

```bash
.venv/bin/python docs/analysis/002-recoverability/notebook.py
```
