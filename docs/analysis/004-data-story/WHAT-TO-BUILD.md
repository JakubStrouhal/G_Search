---
created: 2026-08-07
updated: 2026-08-07
note: Tells the design agent what to produce for the two things its design predates — a contents list and Chapter 5 — and to leave the already-designed chapters alone; carries the argument as one causal chain so the work serves it.
---

# What to build in the explainer, and why

## Read this first — what is designed and what is not

**The supplied design covers the page as it was: four analysis chapters, the replay chapter, and the
limits section. Do not re-open any of them.** Where this document and that design disagree about
appearance, **the design wins**.

**Two things are not in it, and both need you to produce them:**

| | | |
|---|---|---|
| **A contents list** | does not exist at all | the page has six chapters and no navigation |
| **Chapter 5 — "Could a system have known?"** | **written after your design was made** | it is a whole new chapter with components your design has never had to solve |

**Chapter 5 is the real ask.** It is not a copy change to an existing chapter — it is a new section
carrying a result, a two-sided cost, a small evidence table and a three-band split. §4 says exactly
what it must contain and what each part has to do. **Design those elements in the system you have
already built**, so the chapter reads as part of the same document rather than an appendix.

**One consequence to catch:** the chapter formerly labelled *Chapter 5 · try it* is now
**Chapter 6**. If your design shows "Chapter 5" against the replay section, that number is stale.

Everything else here is **what has to be on the page and why** — so the implementation carries the
argument rather than just the markup.

---

## 1. Why the page needs this at all

The page is not hard to follow because it is long. **It is hard to follow because every chapter
exists to answer a question the previous chapter left open, and nothing on the page says so.** A
reader who cannot see that chain reads six disconnected essays and remembers none of them.

So the contents list is not decoration or convenience. **It is the only place the argument is
visible as an argument.** That is why §2 comes before any instruction about what to build.

---

## 2. The argument, as one chain

### What Groupon asked

*What is broken in search?* Nothing further — deciding what to look for was part of the exercise.

### What we had, and the one gap that shapes everything

8,997 searches and 568 deals, joined on market and city. The log records **how many** results came
back. It never records **which**.

That gap is why the page is shaped the way it is: *"this customer was shown the wrong thing"* can
never be **observed** in this data, only inferred. Every chapter is downstream of it, and the last
chapter exists because of it.

### Step 1 — the number a dashboard would report is the wrong number

29.3% of searches return zero results. That is what any dashboard shows.

But searches returning **1–2 results convert at 1.7%**, against **16.1%** for four or more. That is
a cliff, not a gradient — one or two results performs like none. Counting those, the real failure
rate is **52.5%**.

> **Why it matters:** the metric Groupon would report understates the problem by nearly half.
> **Leaves open:** who is supposed to fix it?

### Step 2 — a failure rate names no owner

So we asked a different question — **when a search failed, where was the answer?** There are four
possible answers and they belong to different teams:

| where the answer was | share | whose problem |
|---|---|---|
| nowhere in the market | 43.2% | merchant acquisition — **not search** |
| the user's own city | 32.2% | search |
| another city in the market | 3.1% | product / UX |
| can't tell from this catalogue | 21.5% | not attributed |

> **Why it matters:** it reassigns the problem. The largest single share is not search's to fix, and
> no amount of search work touches it. **This is the finding the whole page exists to deliver.**
> **Leaves open:** when the stock *was* there, why did search still fail?

### Step 3 — the mechanism, observed in production

Groupon's live search matches **fragments of a query, not the query**. `kitesurf` returns a
*"Portable Bartender Barista **Kit**"*. Adding a word does not reliably narrow anything.

So the customer has **no lever** — nothing they type constrains the results — and the system can
never arrive at *"we don't have this"*, because it always has something to show.

> **Why it matters:** this is why the failure is invisible. A dashboard records *"two results
> returned"*. The customer saw nothing usable. Both are true simultaneously, which is why nobody
> catches it.
> **Leaves open:** can you actually prove search is the cause anywhere?

### Step 4 — one slice where cause is demonstrated, not argued

Same concept, same market, same month. Only the **words** change. English phrasing dead-ends
**81.2%** of the time; local phrasing **39.0%**.

> **Why it matters:** it is the one controlled result on the page.
> **Leaves open:** could any system have known in advance?

### Step 5 — so we built one *(the newest chapter)*

Nothing in the supplied data can answer that, for the reason in "what we had": with no query→deal
mapping there is nothing to test detection against.

So we built a system and measured it against the analysis's own labels. **It can detect it** — and
measuring turned up a fault in the analysis itself.

> **Why it matters:** it is the only place the build answers a question the data could not, and it
> converts Step 2 from a diagnosis into something actionable.

---

## 3. Build: the contents list

### The rule

**A list of chapter titles is close to useless here.** *"Chapter 3 — Where was the answer?"* tells a
reader nothing they can use.

**Each entry must carry the finding, not the title.** Someone who reads only the contents list
should still leave with the argument. Treat it as the page's abstract that happens to be navigable.

### The entries — use these lines

| # | Label | Line |
|---|---|---|
| 1 | The reported number is wrong | 1–2 results converts like zero. The real failure rate is 52.5%, not 29.3% |
| 2 | What failure looks like in production | The matcher matches fragments — `kitesurf` returns a barista kit |
| 3 | Where the answer actually was | Four buckets, four owners — and the biggest is not search's to fix |
| 4 | The one slice we can prove | Same concept, same month, different words: 81.2% against 39.0% |
| 5 | Could a system have known? | Yes — and the build found a fault in the analysis |
| 6 | Try it | Replay any of the real queries |
| — | The limits, stated | Where these claims would not survive checking |

### Required behaviour

- **The reader must be able to tell where they are in the chain** while reading. That is the
  contents list's actual job — position in an argument, not a link list. How it is presented is the
  design's call.
- **Chapter 2's entry must say it is a different catalogue.** That chapter is live production
  Groupon, not the supplied data, and the whole package depends on never blurring the two. The
  contents list must not become the one place that distinction is lost.
- **Numbers in these lines are bound, not typed** — see §5. A contents list is a tempting place to
  forget that, and the build will fail if you do.

---

## 4. Design and build: Chapter 5 — the new chapter

**This is the section your design does not cover.** It sits after the language chapter and before
*Replay any real query*. Its label reads **`Chapter 5 · what we built`** — deliberately not *"the
supplied data"*, because it is the one chapter that is not.

### What it needs, as components

Four blocks. Three of them need something the page already does; one is genuinely new.

| Block | What it is | Precedent on the page |
|---|---|---|
| 1 | Two paragraphs of setup | ordinary body copy — nothing new |
| 2 | **Two headline figures**, then a **two-sided cost callout** | Chapter 1 already shows paired headline figures; the callout is the same device as the page's existing notes |
| 3 | **A three-row evidence table**, three columns | the page already has tables in Chapters 3 and 4 |
| 4 | **A three-band proportional split** | Chapter 1's result bands are the same shape — three parts of one whole |

**Nothing here demands a new visual language.** If Blocks 2–4 reuse the treatments you have already
designed for headline figures, notes, tables and bands, the chapter will read as part of the
document. That is the goal — this chapter must not look like a bolted-on result section.

**The one thing to solve deliberately:** this chapter holds the page's **only good news**. Everything
before it reports a failure. It should not be suppressed, but it must not read as a product pitch
either — the page is a report, and a triumphant panel here would undermine the credibility of the
four chapters above it. The good news is also conditional, and the chapter says so twice: once in
Block 2's costs, once in Block 4's narrowing.

### The four blocks, in order

**Block 1 — the question, and why the data cannot answer it.**
Establish that this chapter exists because of the gap in §2: the log holds counts, not deals, so
detection cannot be tested in it. Then state the test in one sentence: **the labels come from the
analysis, the scores come from the build, and neither saw the other.** That independence is what
makes the result mean anything.

**Block 2 — the result, and its cost.**
Two figures: **0.805** separability across all 751 labelled pairs, and **0.934** across the 147 the
analysis is confident about, which carry 90.1% of all search volume.

Then the cost in both directions: **6.8%** of searches for things not stocked would still be shown
results; **23.2%** of searches for things that are stocked would be told we have nothing.

**These two rates must never be combined into one number.** They are different mistakes with
different costs, and a single accuracy figure would hide which one is happening. If the design shows
one summary number here, that is a defect worth raising.

**Block 3 — the fault the build found in the analysis.**

```
score    what was typed          what it matched
0.765    FR sallee de sport      Abonnement Salle de Sport
0.753    DE stadrundfahrt        Stadtführung
0.748    ES limpieza faciaal     Tratamiento Facial
```

**This is the most valuable content on the page.** Each row is a typo the meaning-based match
resolved correctly and the analysis's own hand-built concept map could not — so it is counted as an
*error* while being *right*. The page's argument turns here: **the prototype repairs a weakness in
the analysis that produced it.** Do not let this read as a minor footnote.

**Block 4 — what it does to Chapter 4.**
Three bands showing how far a multilingual model gets on Chapter 4's own pairs: **68.2% bridges ·
18.5% partial · 13.3% does not bridge.**

The closing point must land: **the language gap is real, the fix is partial**, and Chapter 4's
recoverability figure is an **upper bound**, not a forecast. Chapter 5 narrows Chapter 4 — it does
not confirm it.

---

## 5. The data contract — and the rule that will fail your build

**No number may be typed into the page.** Every figure comes from `story_data.json`, injected by
`build_explainer.py`, which **refuses to build** if it finds a hand-typed number in the prose. This
is not a style preference: the repository's recurring defect has been a stale figure living inside a
derived one, and this guard is what stops it. It has already caught a `0.5` written into a sentence
about scores.

Chapter 5 binds to `D.prototype`, sourced from
`../008-threshold-sweep/outputs/summary.json`:

| element id | field | renders |
|---|---|---|
| `pt-pairs`, `pt-pairs-2` | `n_pairs` | 751 |
| `pt-auc` | `auc_all` | 0.805 |
| `pt-auc-conf` | `auc_confident` | 0.934 |
| `pt-conf-n` | `confident_pairs` | 147 |
| `pt-conf-vol` | `confident_volume_share` | 90.1% |
| `pt-fc` / `pt-fa` | `fc_searches` / `fa_searches` | 6.8% / 23.2% |
| `pt-thin` | `fc_on_thin`, `fc_total` | "70 of 71" |
| `pt-typos` | `typo_examples[]` → `{market, q, sim, matched}` | 3 rows |
| `pt-bridge` | `language_bridging.bands[]` → `{band, pairs, en_deads, share}` | 3 bands |
| `lim-bridge`, `lim-fails` | the `bridges` / `fails` shares | inline, in the limits section |

Two further build rules, both already enforced:

- **The page must open from a file with no network.** No CDN, no external font, stylesheet, script or
  image. The build checks.
- **`outputs/explainer.html` is generated. Never hand-edit it** — the next build overwrites it.

---

## 6. Acceptance

Chapters 1–4 and 6 are judged against the supplied design. **Chapter 5 and the contents list are
judged against this list**, plus whether they read as part of the same document.

1. `python3 docs/analysis/004-data-story/build_explainer.py` **exits 0.** If it reports hand-typed
   numbers, the deliverable has failed — that is not a warning.
2. The contents list carries all six chapters plus the limits section, each with **its finding, not
   its title**.
3. The Chapter 2 entry states it is a **different catalogue**.
4. The reader can tell which chapter they are in while scrolling.
5. Every id in §5 is populated in the built file — **no empty bindings**.
6. Chapter 5's typo table shows **three different matched documents**, not three spellings of one.
7. Blocks 2 and 4 present **two rates and three bands** — not one combined figure.
8. The page opens from `file://` with no network and no console errors.
9. No horizontal scroll at any width; wide tables scroll inside their own container.
10. The replay chapter is labelled **Chapter 6**, not Chapter 5.
11. Chapter 5 uses the page's existing treatments for figures, notes, tables and bands — it does not
    introduce a visual language the other chapters do not have.

---

## 7. Files and the build

| Path | Role |
|---|---|
| `explainer.template.html` | The page. Carries no numbers, only a `__STORY_DATA__` token |
| `notebook.py` | Computes everything; emits `outputs/story_data.json` |
| `build_explainer.py` | The only path data takes into the page, and the guard |
| `../008-threshold-sweep/outputs/summary.json` | Chapter 5's source, produced by `sweep.py` |
| `outputs/explainer.html` | Build output. **Never hand-edit** |

```bash
.venv/bin/python docs/analysis/004-data-story/notebook.py
python3 docs/analysis/004-data-story/build_explainer.py
```
