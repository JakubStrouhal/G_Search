---
created: 2026-08-06
updated: 2026-08-06
note: Frontmatter stamped mechanically — replace with one sentence on what changed and why.
---

# 004 — Data story · **this is the deliverable folder**

**Read this folder first. If you only open one file in the whole repo, open
[`outputs/explainer.html`](outputs/explainer.html).**

## What you are looking at

Part A's findings turned into one self-contained web page that a non-technical reader can click
through in ten minutes, and a notebook that shows every calculation behind it. It answers the
question the analysis is spined on: **when a search failed, where was the answer?**

| File | What it is | Show it to Groupon? |
|---|---|---|
| **`outputs/explainer.html`** | **The deliverable.** One page, no server, no kernel, **no network at all**. Opens straight from `file://`. Includes a box that replays any of the real logged queries | **Yes — this is the artifact** |
| `outputs/notebook.html` | The same analysis with the code visible — the "show your working" backup for when someone doubts a figure. Unlike the explainer it is an nbconvert export and pulls MathJax/require.js from a CDN | Yes, as evidence |
| `notebook.py` | Source of truth. Recomputes every figure from the CSVs and emits `outputs/story_data.json`. Runs as a plain script *or* as a `# %%` notebook | Only if asked |
| `explainer.template.html` | The page **with no numbers in it** — carries a single `__STORY_DATA__` token | **No.** On its own it says nothing |
| `build_explainer.py` | Inlines the JSON into the template; refuses to build if the page references anything external | No |
| `outputs/story_data.json` | The contract between notebook and page. Already inlined into the deliverable | No |
| `BRIEF.md` / `RESULT.md` | Working files — the pre-build interview (E1–E8) and the build record | No |

**Why the page has no hand-typed numbers.** The template carries one token; the build step is the
only path data takes into the HTML. This exists because the repo's recurring defect is a stale
figure surviving inside a derived one (the ~18% → ~12% correction happened *during* this build). A
page that hand-typed 18% would still say 18%. The one deliberate exception is labelled: the pinned
**live** observations in Chapter 2 are observations, not computations, and carry host · division ·
date.

## How to read it

`outputs/explainer.html` is six chapters, in argument order:

1. **Half of all searches end in nothing usable** — why the obvious metric (zero-result rate) is the
   wrong one, and what replaces it.
2. **Two results is not the same as "we found it"** — *live production Groupon*, on a dark console,
   behind a banner. **A different catalogue** (see `../003-live-validation/README.md`). It shows the
   failure mechanism; it sizes nothing in the supplied data.
3. **When a search failed, where was the answer?** — the four buckets and their four owners. **This
   is the spine and the slide Part C opens with.**
4. **For one slice we can prove it was the search** — the sizing, reproduced exactly from
   `../002-recoverability/`.
5. **Replay any real query** — type a query, get its real logged counts and its failure class.
6. **The limits, stated** — what the analysis cannot establish.

Read it against `../FINDINGS.md` §5f (the buckets) and §5b (the language test). Those two sections
own the numbers; if the page and FINDINGS ever disagree, **FINDINGS wins**.

### The five figures, and what each is there to settle

Every chart is **inline SVG drawn from `story_data.json` when the page loads** — never an image. A
baked PNG would be a hand-typed number wearing a picture, which is the one defect this page exists
to prevent. All five are hoverable.

| Chapter | Figure | The claim it carries |
|---|---|---|
| 1 | Purchase rate by **exact** result count | The cliff is a step, not a slope — and the missing `3` shows up as a gap in the axis rather than a footnote |
| 2 | Cumulative results by radius | The thin query is **flat at zero at every radius** and still returned results. Drawn in the console palette on purpose — it is a different catalogue |
| 3 | The same dead ends under **all three** readings | **The ordering flip.** This is the page's biggest caveat and the thing to have pre-loaded before presenting |
| 4 | Every matched pair as a slope | 47 fall, 1 rises — countable instead of asserted, with the exception named on the chart |
| 4 | Recovery assumption per class, as ranges | Never quote the midpoint. The supply void is a dot at zero with no range; silent substitution is the only range that **crosses** zero, deliberately |

## The outcome

Over all **4,720 dead ends**, where the answer actually was:

| Where | share | who fixes it |
|---|---|---|
| Nowhere in the market | **43.2%** | Merchant acquisition — *not search* |
| The user's own city | **32.2%** | Search |
| Another city in the market | 3.1% | Product / UX |
| Can't tell from this catalogue | 21.5% | Not attributed |

**The largest bucket is not a search problem.** That is the finding.

## The chart found something, and then killed it — this is the story to tell

Plotting Chapter 1 per *exact* result count exposed what the three-band view hid: **searches
returning 26+ results convert at 2.3%, against 17.8% at 4–25** — 471 searches, 5.2% of all. Adding
them to the dead-end definition would have taken the headline from 52.5% to **57.7%**.

**It was tested and rejected. The tail is a generation artifact and the headline does not move.**
Which searches land above 25 is flat across market, city, coverage and language — indistinguishable
from a coin flip (χ² p = 0.65). The decisive test: across the **123 market+query pairs seen in both
bands**, the *same* query converts at **18.3%** when it lands 4–25 and **2.6%** when it lands 26+
(106 of 123 lower, p = 6×10⁻²³). Nothing about the query changed, so the rate belongs to the drawn
count, not to the search.

**Two things here are worth saying out loud rather than burying:**

1. **The same test validates the ≤2 rule.** Landing in 1–2 *is* predicted by the query
   (χ² p = 4×10⁻¹⁶), most sharply by what language it is asked in. Same method, opposite answer —
   which is exactly why 52.5% survives and 57.7% does not.
2. **The first reading was wrong, and is recorded as wrong.** It was initially called the
   silent-mismatch signature, on a query list that turned out to be an artifact of not grouping by
   market. `FINDINGS.md` §9 row 13. The brief grades whether claims survive checking — this one did
   not, and the register is the evidence that it *was* checked.

`INDEX.md` 6.6 is **closed**. `FINDINGS.md` §0 (the seam), §8 (the quoting rule), §9 row 13.
## The one caution to have pre-loaded before you present this

**Never quote 43.2% on its own. Quote the band [43.2%, 64.7%].** One tier of the coverage test
(`plausible` — a generic deal that *might* answer the query) is a judgement call, and all 1,016 of
its dead ends move together. Under one of the three readings the ordering **flips** and same-city
overtakes nowhere. The page prints the whole band and names the flip on purpose. `INDEX.md` known
issue #13; `../FINDINGS.md` §5f.

The decomposition still beats a shuffled null under **every** reading (excess +9.8pp to +14.0pp,
z = 19.5 to 33.6) — that permutation test is what licenses the claim at all.

## The evidence chain, end to end

This is the answer to "how did you come to that conclusion":

```
docs/brief/{search_log,deals}.csv          ← exactly what Groupon supplied, never written to
  → docs/analysis/{validate,classify,language_test}.py
  → docs/analysis/outputs/*.csv            ← query_classes.csv, inventory_location.csv, …
  → 002-recoverability/notebook.py         ← the sizing
  → 004-data-story/notebook.py
  → 004-data-story/outputs/story_data.json
  → 004-data-story/outputs/explainer.html  ← the page
```

Every number on the page traces back up that chain to a script and a CSV. Nothing is asserted from
memory.

## Rebuild

```bash
.venv/bin/python docs/analysis/004-data-story/notebook.py
```

```bash
python3 docs/analysis/004-data-story/build_explainer.py
```

## What this folder does **not** do

- **It is not Part B.** No embeddings, no semantic matching, no threshold sweep. The replay box is a
  lookup against `query_classes.csv`; a query outside the log is **refused, not modelled**. That
  refusal is deliberate — the brief grades what the system does when it has no good answer.
- No visual-design claims. Explicitly ungraded; the page is legible, not decorated.
- Three contested figures are **excluded on purpose** (`RESULT.md` § "Contested numbers"): the
  adrenaline share of zeros, the supply-void aggregate pair count, and the pair universe. Chapter 3
  quotes per-cell counts instead — identical under either competing rule.
