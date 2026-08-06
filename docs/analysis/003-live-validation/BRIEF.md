# Live validation of the recoverability model — before any build

Opened 2026-08-06.

## The question

The notebook (`002-recoverability/`) turns Part A into a decision: *search work is ~18% of the
recoverable opportunity; the rest is merchant acquisition.* That conclusion is about to justify a
Supabase + Vue3 build. **Every input to it comes from a synthetic dataset**, and four of its inputs
are mechanisms rather than measurements. Live Groupon can test the mechanisms.

**What live recon can and cannot do — the line that must not blur.** It can confirm *how a real
search engine fails*, which is what F1–F6 describe. It **cannot** validate any number in the
supplied dataset, because they are different catalogues. `PLAN.md` §7 already lists conflating the
two as a trap. Every finding here gets tagged with which catalogue it is about.

## Why now

Before the build, not after. Two of the checks below can **change a number in the notebook**, and
one can change what Part C is allowed to claim. Finding that out after `supabase/` exists is
finding it out too late.

## Pre-registered predictions

Written **before** probing, so a miss is visible rather than narrated away. Each says what it
predicts, what would falsify it, and — the part that matters — **what changes if it fails**.

### P1 · F1: a real-but-unstocked word is as inert as gibberish
- **Predicts:** `paintball massage` returns the same count as `massage`, just as `xqzjw massage`
  did (458 = 458, already observed).
- **Falsified if:** the count drops. Then the discriminating term *does* constrain, and F1 is
  weaker than the spec claims.
- **If it fails:** F1's screen behaviour in `001-part-b/SPEC.md` §3 needs re-justifying, and the
  "name the token that could not be matched" differentiator loses its live evidence.
- **Why it matters most:** F1 is the class the spec calls the invisible failure, and its only
  *observed* proof is one query pair. One pair is an anecdote.

### P2 · F2: the multi-token diacritic penalty replicates
- **Predicts:** across more PL pairs and the DE/FR/ES equivalents, stripping diacritics costs far
  more on multi-token queries than single-token (observed: −41% vs −8.8%).
- **Falsified if:** the penalty is flat, or single-token is worse.
- **If it fails:** **this is the expensive one.** F2's 52% recoverability is the notebook's *only*
  measured anchor. Losing the mechanism doesn't invalidate the 81.2/39.0 gap — that is measured in
  the supplied data — but it removes the reason to believe it generalises, and the notebook should
  widen F2's range to match F3 and F5.

### P3 · F4: does live Groupon actually stock adrenaline in these cities?
- **Predicts:** **yes, abundantly** — London/Berlin/Paris almost certainly have skydiving,
  helicopter and balloon inventory.
- **If confirmed** (the likely case): the supplied catalogue's void is a **modelling choice, not a
  description of Groupon's real assortment**. That does not kill the finding, but it hard-bounds
  what Part C may claim. The transferable result becomes *"here is a method for detecting supply
  voids from search logs, and here is what it finds in the supplied data"* — not *"Groupon should
  go sign skydiving vendors in London."*
- **Why it matters:** this is the check most likely to embarrass if a grader runs it and we have
  not. It costs one search. Getting to it first and stating the limit converts a vulnerability into
  the honesty the brief explicitly grades.

### P4 · F5: does live Groupon ever return exactly 3 results?
- **Predicts:** yes, routinely.
- **If confirmed:** the supplied data's 0,1,2,→4 gap is a **generator artifact, not a ranking
  cutoff**. F5 is then a mislabelled class, its 353 dead ends are not evidence of a threshold, and
  **its 40% recoverability assumption has no basis** — the notebook's central estimate falls from
  ~59 to ~36 purchases/month. This directly rewrites a number.
- **If falsified** (live also never returns 3): a genuinely interesting cross-catalogue pattern
  worth a line in Part C.

### P5 · F3: does live Groupon widen radius with distance framing?
- **Predicts:** it surfaces nearby-city inventory with distance stated.
- **If confirmed:** F3's proposed fix is table stakes, not a differentiator — demote it in the
  prototype and say so.
- **If falsified:** F3's fix is a real gap, and the prototype's version is worth more.

### P6 · The `SuggestedSearchQueries` 500
- Pending 1.7(b). Re-check on another day/network before quoting it as a production defect.

## Constraints

- **Read-only.** Replay the public GraphQL query via `docs/analysis/live_probe.js`; no accounts, no
  writes, no load. Pace requests like a human.
- **Exact counts only.** The UI shows buckets ("400+"), and reasoning from buckets already produced
  two wrong claims in this repo.
- **Pin every observation** — market, city, query string, date. An unpinned number is how the "4×
  diacritic penalty" claim went wrong the first time.
- Time budget: **~45 minutes.** This is validation, not a second reconnaissance pass.

## Done looks like

1. Each P1–P6 marked **confirmed / falsified / inconclusive**, with the exact counts.
2. `002-recoverability/notebook.py` updated where a prediction changed an input — specifically the
   F5 assumption, which is the one most likely to move.
3. `FINDINGS.md` gains the live results, tagged for **which catalogue** they describe.
4. `001-part-b/SPEC.md` amended if P1 or P5 changes a required behaviour.
5. A one-line verdict: **does the ~18% conclusion survive?**

## What would make this unnecessary

Nothing — but note that P3 is the only one whose likely outcome (*confirmed*) constrains Part C
rather than improving it. Run it anyway. A limit found by us is honesty; the same limit found by
the grader is a hole.
