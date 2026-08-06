# Groupon case study R29944 — Discovery, International

Submission for **Senior Product Manager, AI (Discovery, International)**.

The brief supplies a month of search logs from five international markets and the
deal inventory those searches ran against, and deliberately declines to say what
to look for. Everything below comes out of that data or out of Groupon's live
production search — every number is traceable to a script in this repo.

---

## Start here

| If you want to… | Read / run |
|---|---|
| Check the analysis yourself | `python3 docs/analysis/validate.py` |
| Re-derive the **live** production numbers | `docs/analysis/live_probe.js` (see below) |
| See the verified findings | `docs/analysis/FINDINGS.md` |
| See the reasoning behind it | `docs/analysis/PLAN.md` |
| See what is done, pending, and what was decided | `INDEX.md` |

```bash
python3 docs/analysis/validate.py          # requires pandas + numpy; runs from anywhere
```

The script is a linear sequence of `LAYER` blocks, each printing its own counts,
so any headline number can be traced to a line. To read one section:

```bash
python3 docs/analysis/validate.py | sed -n '/LAYER 3 /,/LAYER 4 /p'
```

**`live_probe.js` is not run with node.** Paste it into the DevTools console on a
`groupon.co.uk` or `groupon.pl` page, then `await probeGB()` / `await probePL()` /
`await probeSuggest()`. It replays Groupon's own persisted GraphQL query to read
exact result counts, because the UI only shows rounded buckets ("400+"), and
reasoning from those buckets produced two wrong claims in an earlier draft.

---

## Layout

```
docs/brief/       Exactly what Groupon supplied — the PDF, search_log.csv, deals.csv.
                  Immutable input; nothing writes back to it.
docs/analysis/    The work: FINDINGS.md (verified claims), PLAN.md (reasoning),
                  validate.py / classify.py / language_test.py / live_probe.js.
        outputs/  Generated CSVs. Regenerable, never hand-edited.
        <nnn>-*/  One folder per unit of work: BRIEF.md -> SPEC.md -> RESULT.md.
                  Working files, not deliverables.
INDEX.md          Status, queue, defects, decisions.
```

**The three deliverables are** `docs/analysis/FINDINGS.md` (Part A), the hosted prototype
(Part B), and the writeup (Part C). The numbered folders are how they got built.

---

## What is broken

**The readable version of all of this is
[`docs/analysis/004-data-story/outputs/explainer.html`](docs/analysis/004-data-story/outputs/explainer.html)**
— one self-contained page, no kernel, with a box that replays any of the 613 real
queries. Open that first. This section is the summary; `FINDINGS.md` owns the
numbers and their caveats, and nothing here is restated that lives there.

**1. The obvious metric is the wrong one.** 29.3% of searches return zero results
— but a search returning **1–2 results converts at 1.7%**, against 16.1% at four
or more. A cliff, not a gradient. **The defensible headline is 52.5%**, and it
survives stratification within concept × city (it moves the purchase rate by
0.02pp, and holds in 137 of 138 strata).

**2. One question sorts the failures, and the answer names the owner.** For every
one of the 4,720 dead ends: *where was the answer?*

| Where the answer was | dead ends | share | who fixes it |
|---|---|---|---|
| Nowhere in the market | 2,039 | **43.2%** | Merchant acquisition — not search |
| The user's own city | 1,520 | **32.2%** | Search |
| Another city in the market | 145 | 3.1% | Product / UX |
| Can't tell from this catalogue | 1,016 | 21.5% | Not attributed |

The largest bucket is not a search problem at all. **Quote the `nowhere` band
[43.2%, 64.7%], not one end** — one tier of the coverage test is a judgement call
that moves 1,016 dead ends together, and under one reading the ordering flips.
The decomposition beats a shuffled null under every reading (excess +9.8pp to
+14.0pp, z = 19.5 to 33.6). `FINDINGS.md` §5f.

**3. The strongest single result: phrasing, measured.** The brief's own thesis is
that the platform was built for English-language queries. Matched pairs — same
concept, same market, only the words change — give **81.2% dead-end in English vs
39.0% in the local language**, a 42.3pp gap across 47 of 48 pairs. Both confounds
were killed: loanwords for unstocked concepts fail at the ordinary 44.0%, and rare
*local* queries die at 53.3%, not 81%.

**4. Sizing, with the denominator attached.** Today: **723 purchases/month** across
five markets. Fixing every class we can name returns **+36/month (+5.0%)** — about
**12%** of the recoverable opportunity. The supply-void ceiling is **+271 (+37.5%)**.
Every way of tightening the search side lowers it further (7.8%, then 5.7%); the
most generous figure is the one published.

**5. It is not one broken country**, and **typos are a red herring** — market
zero-rates run 26.9% (DE) to 32.6% (PL) with only that pair non-overlapping, and
typos are 1.9%–7.5% of zeros depending on definition, most already resolving.

## What production search actually does

Tested against live Groupon. **The live catalogue is not the supplied dataset** —
this shows how a real search engine fails; it validates no number in the data.

`skydiving` on `groupon.co.uk/browse/london` (2026-08-06) returns **2 deals**: an
online COSHH workplace-safety course, and a real skydive **141.5 miles away in
Devon**. For a customer in London that is nothing — but every dashboard behind it
records a successful search. The matcher matches *fragments*: `kitesurf` returns a
"Portable Bartender Barista **Kit**".

That is the whole point of the question in §2: **a result count cannot tell you
whether search worked.** The API confirms why — it returns no relevance score, no
matched-term field and no spell-correction field, so the client cannot distinguish
a genuine match from padding. The supplied dataset's central limitation is not a
weakness of the sample; it reproduces what the platform actually exposes.

Two claims from an earlier draft of this file were **withdrawn** after checking,
and the corrections are in `003-live-validation/RESULT.md`: "a word that matches
nothing is completely inert" (true for nonsense, false for real words — one
*removed* 40 results), and a general two-word diacritic penalty (it replicates
exactly for the `masaż` family and not at all for three other Polish pairs).

---

## How to think about it

Every search is a cell in a grid of **what supply exists** × **how the system
responded**. The zero-result metric only ever sees the "returns nothing" column —
a full page of confident, wrong results is invisible to it.

There are two cuts of that grid and they nest rather than compete. **"Where was the
answer?"** (§2 above) is the one to lead with: four buckets, four owners, and it is
the question that decides where engineering effort goes. **F1–F6** sits underneath
it as the mechanism detail — *why* each failure happened — and the prototype's
required behaviours are keyed to those classes. `nowhere` is exactly F1 ∪ F4, and
that nesting is asserted in code rather than claimed. Full treatment of F1–F6 in
`docs/analysis/PLAN.md` §5; of the buckets in `FINDINGS.md` §5f.

Two of the six class *names* have been withdrawn while keeping their populations:
**F5 "ranking cutoff"** (the live probe showed Groupon returns exactly 3 routinely,
so the inference behind it was dead) and **F3 "geographic thinness"** (only 6 of
its 321 dead ends actually have the deal in another city). Both are now residuals
with no established cause, which is a smaller claim than the one they replaced.

---

## Honest limits

**The structural one:** `results_shown` is a bare count. There is no query→deal
mapping and no relevance score, so any claim about *which* deals a query returned
is inference from category structure, not observation. This is why this repo
contains a supply-side **coverage-gap** analysis and not a sizing of "how many
searches got wrong results" — the latter is not provable from this data.

**Not testable at all with what was supplied:** the revenue and AOV claims (no
order data), and "thinner inventory" in absolute terms (no US baseline).

**Data quality flags:** no search anywhere returns exactly 3 results — the
distribution runs 0, 1, 2, then jumps to 4. Zero nulls, zero duplicate IDs, no
funnel-impossible rows. Consistent with synthetic generation; stated rather than
smoothed over.

**Claims retracted during the work**, kept visible because the brief grades
whether claims survive checking: an initial "silent token-dropping" mechanism
(disproved — dropping a term cannot raise a result count), a follow-up "unstocked
words widen results" claim (overreach — measured a union, not query semantics),
and a "4× diacritic penalty" read off rounded UI labels with an unpinned location
(real figures: 162 vs 95).

---

## Status

**[`INDEX.md`](INDEX.md)** — the board for Parts A/B/C, the open work queue, the known-defect list,
and the last six decisions with the reasoning behind them.

Status is stated there and nowhere else, deliberately: it previously lived in four files and had
drifted to four different answers.
