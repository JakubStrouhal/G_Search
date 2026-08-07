---
created: 2026-08-07
updated: 2026-08-07
note: Addendum to REDESIGN-BRIEF.md — adds the chapter that did not exist when it was written, and a table of contents, because the page grew past the length a reader can hold without one.
---

# Addendum — the table of contents, and Chapter 5

**Read `REDESIGN-BRIEF.md` first.** It governs the visual system, the three build gates and the
component inventory, and none of it is superseded here. This file adds two things it could not
cover: a **chapter that did not exist when it was written**, and a **table of contents**, which the
page now needs because it has six chapters and no way to see them.

**Hand both files to the agent.** This one second.

---

## 1. Why the page is hard to follow, and what actually fixes it

The page is not hard to follow because it is long. It is hard to follow because **each chapter
exists to answer a question the previous chapter opened**, and nothing on the page says so. A reader
who cannot see that chain reads six disconnected essays.

So the fix is not decoration. **It is making the chain visible.** That is what the table of contents
is for, and it is why §2 below is written before any layout instruction.

---

## 2. The argument, as one causal chain

**Give this to the agent verbatim.** Every navigation and layout decision should serve it.

### What Groupon asked

*What is broken in search?* No further guidance — deciding what to look for was part of the test.

### What we had to work with, and the one gap that shapes everything

8,997 searches and 568 deals, joined on market and city. The log records **how many** results came
back. It never records **which**.

That single gap is why the page is shaped the way it is. It means *"this user was shown the wrong
thing"* can never be observed in this data — only inferred. Every chapter is downstream of it.

### Step 1 — the number a dashboard would report is the wrong number

29.3% of searches return zero results. That is what any dashboard shows.

But searches returning **1–2 results convert at 1.7%**, against **16.1%** for four or more. That is
not a gradient, it is a cliff: one or two results performs like none at all. Counting those, the
real failure rate is **52.5%**.

> **Why it matters:** the metric Groupon would report understates the problem by nearly half.

### Step 2 — "half of searches fail" does not tell anyone what to do

A failure rate names no owner. So we asked a different question — **when a search failed, where was
the answer?** — and that has four possible answers, each belonging to a different team:

| where the answer was | share | whose problem |
|---|---|---|
| nowhere in the market | 43.2% | merchant acquisition — **not search** |
| the user's own city | 32.2% | search |
| another city in the market | 3.1% | product / UX |
| can't tell from this catalogue | 21.5% | not attributed |

> **Why it matters:** it reassigns the problem. The largest share is not search's to fix, and no
> amount of search work touches it. This is the finding the whole page is built to deliver.

### Step 3 — when the stock *was* there, why did search still fail?

Production Groupon, probed directly, shows the mechanism: **the matcher matches fragments of a
query, not the query.** `kitesurf` returns a *"Portable Bartender Barista **Kit**"*. Adding a word
does not reliably narrow anything.

So the user has **no lever** — nothing they type constrains the results — and the system can
therefore never reach *"we don't have this"*. It always has something to show.

> **Why it matters:** this is why the failure is invisible. A dashboard records "two results
> returned." The customer saw nothing they could use. Both are true at once.

### Step 4 — for one slice, we can prove search was the cause

Same concept, same market, same month. Only the **words** change. English phrasing dead-ends
**81.2%** of the time; local phrasing **39.0%**.

> **Why it matters:** it is the one controlled result on the page — the only place cause is
> demonstrated rather than argued.

### Step 5 — but could a system ever have *known*? *(the new chapter)*

Everything above stops at a diagnosis. Nothing in the supplied data can say whether a system could
have **detected** any of it — because of the gap in "what we had": no query→deal mapping means
there is nothing to test detection against.

So we built one and measured it. **It can.** And measuring it turned up a fault in the analysis
itself.

> **Why it matters:** it is the only place the build answers a question the data could not, and it
> is what turns Step 2's finding from a diagnosis into something actionable.

### The shape to communicate

```
   the gap: counts, never which deals
        │
   1 ── the reported number is wrong ──────────► 52.5%, not 29.3%
        │        (…but who fixes it?)
   2 ── where was the answer? ─────────────────► four owners
        │        (…why did search fail when stock existed?)
   3 ── the mechanism, live ───────────────────► fragments, no lever
        │        (…can you prove it is search?)
   4 ── the language test ─────────────────────► 81.2% vs 39.0%
        │        (…could a system have known?)
   5 ── we built it ───────────────────────────► yes, and here is the cost
```

---

## 3. The table of contents

### The rule that makes it work

**A contents list of chapter titles is close to useless here.** *"Chapter 3 — When a search failed,
where was the answer?"* tells a reader nothing they can act on.

**Each entry must carry the claim, not the title.** The reader should be able to read the TOC alone
and come away with the argument. Treat it as the page's abstract that happens to be navigable.

### Content — one line each, and each line is a finding

| # | Label | The line that must appear |
|---|---|---|
| 1 | The reported number is wrong | *1–2 results converts like zero. The real failure rate is 52.5%, not 29.3%* |
| 2 | What failure looks like in production | *The matcher matches fragments. `kitesurf` returns a barista kit* |
| 3 | Where the answer actually was | *Four buckets, four owners — and the biggest is not search's to fix* |
| 4 | The one slice we can prove | *Same concept, same month, different words: 81.2% vs 39.0%* |
| 5 | Could a system have known? | *Yes — and the build found a fault in the analysis* |
| 6 | Try it | *Replay any of the real queries* |
| — | The limits, stated | *Where these claims would not survive checking* |

Chapter 2's entry **must carry its own catalogue warning** — it is live production Groupon, a
different catalogue from the supplied data, and `REDESIGN-BRIEF.md` R2 keeps that distinction
visually. **The TOC must not be the one place the distinction is lost.**

### Behaviour

- **Sticky on desktop**, so the reader always knows where they are in the chain. Collapsed to a
  disclosure on mobile — do not consume vertical space on a phone.
- **Current chapter highlighted** as the reader scrolls. This is the whole point: the TOC's job is
  to show *position in an argument*, not to be a link list.
- **`REDESIGN-BRIEF.md` Gate 1 applies** — no scroll library, no external anything.
  `IntersectionObserver` is native and sufficient.
- **Numbers in the TOC lines are bound, not typed.** Gate 2 applies here exactly as in the body, and
  a contents list is a tempting place to forget it. Bind to the same ids the chapters use.
- Do **not** number the entries in a way that fights the `.chno` labels already in the body.

---

## 4. Chapter 5 — what it must contain

Sits between the language chapter and *Replay any real query*. `.chno` reads
**`Chapter 5 · what we built`** — deliberately not *"the supplied data"*, because this is the one
chapter that is not.

### The four blocks, in order

**Block 1 — the question, and why the data cannot answer it.**
Two short paragraphs. Must establish that this chapter exists because of the gap named in §2: the
log has counts, not deals, so detection is untestable in it. Then the test in one sentence — *the
labels come from the analysis, the scores come from the build, neither saw the other.*

**Block 2 — the result.** Two large figures, using the existing `.nums` treatment from Chapter 1:

- `0.805` — separability across all 751 pairs
- `0.934` — on the 147 labels the analysis is confident about, which carry 90.1% of search volume

Then a callout in both directions, and **the two rates must never be averaged into one** — the note
already says why, keep it: they are different mistakes, and one number would hide which is happening.

**Block 3 — the fault the build found in the analysis.** A three-row table:

```
score    what was typed          what it matched
0.765    FR sallee de sport      Abonnement Salle de Sport
0.753    DE stadrundfahrt        Stadtführung
0.748    ES limpieza faciaal     Tratamiento Facial
```

**This block is the most valuable content on the page and the easiest to under-design.** Each row is
a typo the meaning-based match resolved correctly and the analysis's own hand-built concept map
could not — so it is scored as an *error* while being *right*. The page's argument turns here: the
prototype repairs a weakness in the analysis that produced it. Give it room.

**Block 4 — narrowing Chapter 4.** A three-band bar (reuse Chapter 1's band grammar) showing how far
a multilingual model gets on Chapter 4's own pairs: **68.2% bridges · 18.5% partial · 13.3% does not
bridge.** The closing line must land: the gap is real, the fix is partial, and Chapter 4's figure is
an **upper bound** rather than a forecast.

### Register

**`REDESIGN-BRIEF.md` R1 governs: this is a report, not a product surface.** Chapter 5 is the most
tempting place to break that — it is the "our solution works" chapter — and a confident-looking
result panel would read as marketing. It should look like the rest of the evidence.

There is one asymmetry worth designing for: Chapter 5 contains the page's **only good news**. Do not
suppress that, but do not let it outshine Chapter 2's failure exhibit either. The good news is
conditional and the page says so twice — the costs in Block 2, the narrowing in Block 4.

---

## 5. The data contract for Chapter 5

Everything binds to `D.prototype`, sourced from
`docs/analysis/008-threshold-sweep/outputs/summary.json` via `notebook.py`. **This is a data source
that did not exist when `REDESIGN-BRIEF.md` §8 was written** — add it there, do not replace it.

| element id | binds to | renders as |
|---|---|---|
| `pt-pairs`, `pt-pairs-2` | `n_pairs` | 751 |
| `pt-auc` | `auc_all` | 0.805, three decimals |
| `pt-auc-conf` | `auc_confident` | 0.934 |
| `pt-conf-n` | `confident_pairs` | 147 |
| `pt-conf-vol` | `confident_volume_share` | 90.1% |
| `pt-fc` / `pt-fa` | `fc_searches` / `fa_searches` | 6.8% / 23.2% |
| `pt-thin` | `fc_on_thin`, `fc_total` | "70 of 71" |
| `pt-typos` | `typo_examples[]` — `{market, q, sim, matched}` | 3-row table |
| `pt-bridge` | `language_bridging.bands[]` — `{band, pairs, en_deads, share}` | 3 bands |
| `lim-bridge`, `lim-fails` | the `bridges` / `fails` band shares | inline, in the limits section |

**A comp may show these values. A comp may not typeset them as final.** Gate 2 is absolute: the
build fails if any figure is typed into the template. It already caught a `0.5` written into prose
about AUC scores during the first build of this chapter — which is exactly what it is for.

---

## 6. Acceptance — additional to `REDESIGN-BRIEF.md` §10

1. `python3 docs/analysis/004-data-story/build_explainer.py` **exits 0.** If it reports hand-typed
   numbers, that is the deliverable failing, not a warning.
2. The TOC lists all six chapters plus the limits section, each carrying **its claim, not its title**.
3. The TOC entry for Chapter 2 states it is a **different catalogue**.
4. The current chapter is visibly marked while scrolling, and the TOC does not obstruct content at
   any width.
5. Every id in §5 is populated in the built file — **no empty bindings**.
6. Chapter 5's typo table shows **three distinct matched documents**, not three spellings of one.
7. No horizontal scroll at any width; wide tables scroll inside their own container.

---

## 7. Files

| Path | Role |
|---|---|
| `REDESIGN-BRIEF.md` | **Read first.** Visual system, gates, components, fonts |
| `explainer.template.html` | The page. Carries no numbers, only `__STORY_DATA__` |
| `notebook.py` | Computes everything; emits `outputs/story_data.json` |
| `build_explainer.py` | The only path data takes into the page. **Enforces Gate 2** |
| `../008-threshold-sweep/outputs/summary.json` | Chapter 5's source. Regenerated by `sweep.py` |
| `outputs/explainer.html` | Build output. **Never hand-edit** |

```bash
.venv/bin/python docs/analysis/004-data-story/notebook.py
python3 docs/analysis/004-data-story/build_explainer.py
```
