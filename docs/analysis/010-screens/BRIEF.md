---
created: 2026-08-07
updated: 2026-08-07
note: Opens the screens unit — measures what the four behaviour states actually cost in traffic before anything is designed, and puts ten decisions in front of the owner rather than resolving them unilaterally.
---

# The screens — what a person actually sees

Opened 2026-08-07. **Plan only. Nothing here is decided, and nothing is built.**

**This brief is written to be argued with.** §5 is ten open decisions; I have a recommendation for
each and none of them is settled. The point is to be certain before building, not fast.

## The question

The backend is finished. `search_deals(market, city, query)` returns a band, the matched document,
the deals, and Part A's independent verdict on the same query. **Nothing renders it.**

The brief's central requirement is *a working, clickable prototype, not a deck* — and it is explicit
that **what it does when it has no good answer tells us as much as what it does when it has one.**
So the question is not "what screens do we need". It is:

> **Which behaviours must a person be able to trigger and see, and how few screens can carry them?**

## Why now

`INDEX.md` 4.1: steps 1–5 of 10 are built. Step 4 gated the UI and has passed. Every remaining item
in Part B is presentation, and **Part C cannot be honestly written until a prototype exists**,
because two of its four required bullets describe what was built.

## What we know — measured, not assumed

These numbers decide how much design each state deserves. Run against the loaded database today.

### The three bands, over all 751 labelled pairs

| band | pairs | searches | share of volume |
|---|---|---|---|
| **abstain** — below LOW | 419 | 4,198 | **46.7%** |
| **confident** — at or above HIGH | 178 | 2,916 | 32.4% |
| **adjacent** — between | 154 | 1,883 | 20.9% |

**All three fire, and none is a rounding error.** The three-band design is real rather than
theoretical, and *abstain is the single largest state* — the prototype spends more of its time
saying "we don't have this" than showing results. That is the finding, arriving as a UI fact.

### What a city actually returns — all 12,260 city × query combinations

| state | combos | share |
|---|---|---|
| **0 results** — honest empty state | 7,756 | **63.3%** |
| **3+ results** — ordinary results page | 3,094 | 25.2% |
| **1–2 results** — near-empty | 1,410 | **11.5%** |

The near-empty state is **not an edge case**. It is a ninth of everything, and `FINDINGS.md` §1 is
why it needs its own treatment: 1–2 results converts at 1.7% against 16.1%, so rendering it as an
ordinary results page is the invisible failure being rebuilt.

### Other facts that constrain the design

- **613 queries have embeddings; anything else is refused by name.** Free-text input will hit that
  refusal often. That is either the most honest thing on the page or the most frustrating,
  depending entirely on how it is presented.
- **20 market × city pairs.** The user must set that context before any search means anything.
- **The band and Part A's class disagree on some queries** — `manicura` (ES) is the live example:
  Part A says stocked, the band abstains. The RPC returns `band_agrees_with_part_a` for exactly this.
- **Every abstention already writes a demand row.** The loop closes server-side whether or not a UI
  element exists for it.

## What would change the answer

Checked first, as the brief's own rule requires.

| If this were true | The unit changes |
|---|---|
| Any band never fired | that screen would be theatre — **checked: all three fire** |
| The near-empty state were rare | it would fold into the results page — **checked: 11.5%** |
| The design were unavailable | we would ship rough-but-working, which the brief explicitly permits |
| Part C were nearly done | screens would be the priority anyway — **it is at zero, and this is a dependency of it** |

Nothing here makes the work unnecessary.

## Constraints

- **Must stay true:** the failure class comes from `query_classes`, never from the threshold (D1).
  The UI presents both and shows the disagreement.
- **Must stay true:** abstention is a first-class outcome, not an error state. It is 46.7% of volume
  and the graded requirement.
- **Must stay true:** keys stay server-side; the browser holds the publishable key and the only
  write path is `demand_events`.
- **Not assessed:** code quality, tests, visual design. *"Ship the rough thing that works."*
- **Budget is the real constraint.** Output per hour is graded and more hours is explicitly not a
  better score. Every screen must earn itself against Part C's remaining time.

## Open decisions — this is the part to argue with

My recommendation is given so there is something to push against, **not because it is settled.**

| # | Decision | My lean | The tension |
|---|---|---|---|
| **1** | How many screens? `006 SPEC` §3.1 lists S1–S7 + S6a | **Four behaviour states, not seven screens** — confident, near-empty, adjacent, abstain. S1/S6 are the same screen with different content | Seven named screens reads thorough; four states is what the code actually has. Which does a grader reward? |
| **2** | One scrolling page, or routes? | One page, prototype as a live section | `006` assumed one page. Routes make the prototype feel like a product; one page keeps the argument intact |
| **3** | Free-text input, or curated chips? | **Both** — chips lead, free text allowed, refusal shown proudly | Free text hits the 613-query refusal constantly. Is that honesty on display, or a broken demo? |
| **4** | Who picks market + city? | A persistent selector, defaulted to GB/London | Twenty combinations is a lot of surface for a demo that only needs five |
| **5** | Staff panel: always on, toggle, or separate view? | **Toggle, default on** | It is the highest-value component for this audience and the literal answer to "show your working" — but it is also not what a customer sees |
| **6** | Does near-empty get its own screen? | **Yes** — 11.5% and it is the headline finding | It costs a screen for something that looks like a results page with fewer rows |
| **7** | How far does the acquisition brief (S5) go? | A table plus one mocked brief for the top cell | It maps to Groupon's named growth driver, but it is the furthest thing from search |
| **8** | Coverage table — its own page, or a section? | A section, always visible | `001 SPEC` §4 calls it a required deliverable. Burying it loses the point |
| **9** | Use the design agent's output, or ship rough? | **Rough first, design if it lands in time** | Visual design is explicitly not assessed, and a half-applied design looks worse than none |
| **10** | Does notify-me exist, given abstention already writes? | Yes, as a **separate** signal | Two signals is honest — "we had nothing" and "tell me" are different. It is also more to build |

## Done looks like

1. Every decision above resolved **with its reason**, in a SPEC, before any component is written.
2. Each of the four behaviour states reachable by a named query in five markets.
3. The staff panel shows the band, the matched document, Part A's class, and **whether they agree**.
4. A grader can trigger the abstain path and see the demand row it wrote.
5. Nothing on the page implies a number the analysis does not support.
