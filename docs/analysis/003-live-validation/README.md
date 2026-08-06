# 003 — Live validation · **a different catalogue. Read this line before anything else.**

> ⚠️ **Everything in this folder describes live production Groupon — `groupon.co.uk` and
> `groupon.pl`, 2026-08-06. It is NOT the supplied dataset.** It shows how a real search engine
> fails. It **validates no number** in the CSVs and sizes nothing.
>
> The trap, and it is a real one: **live GB stocks paintball (12 deals) and sushi (28).** The
> supplied dataset says both are stocked nowhere. If you present the two as one evidence chain,
> you will assert that Groupon lacks paintball, and that is false. `INDEX.md` known issue #11.

## What you are looking at

Six predictions (P1–P6) were **written down before any of them was run**, each with the observation
that would falsify it. Then Groupon's own persisted GraphQL query was replayed read-only in the
browser console to get exact result counts — the UI only shows rounded buckets ("400+"), and
reasoning from those buckets had already produced two wrong claims in an earlier draft.

| File | What it is | Show it to Groupon? |
|---|---|---|
| **`RESULT.md`** | **What was found, prediction by prediction — including the two that were falsified.** The presentable file of this folder | **Yes — and the falsified ones are the point** |
| `BRIEF.md` | The pre-registered predictions and falsifiers, written before the run | Yes, to prove they were pre-registered |
| `QUERIES.md` | The exact query list and instrument-control procedure | Only if asked |
| `../live_probe.js` | The instrument. **Not run with node** — pasted into DevTools on a Groupon page, then `await probeGB()` / `await probePL()` | Only if asked |

## How to read it

Read `RESULT.md` top to bottom. It is short, and it is organised as *prediction → what was observed
→ verdict*. Two things to notice as you go:

- **The instrument-check table at the top.** Before trusting any number, a junk division name was
  sent to each host to prove the real one was really being read. A typo'd division **fails silently**
  — no error, just a wrong number — so every cross-market comparison without this control is
  confounded and looks fine (`INDEX.md` known issue #9). This is the methodological detail most
  worth pointing at in an interview.
- **The verdicts are mixed on purpose.** P3 and P4 confirmed. P1 falsified *into something stronger*.
  P2 replicates exactly but does not generalise. P5 falsified helpfully. P6 replicated on a second
  host and day.

## The outcome

**The single most valuable result was not predicted at all: silent substitution, observed rather
than inferred.** The supplied log has no query→deal mapping, so `FINDINGS.md` §3 could only tag
"paintball returns escape rooms" as CANNOT VERIFY. Live Groupon has that mapping, and the titles
show the mechanism directly:

| query on `groupon.co.uk/browse/london` | what came back |
|---|---|
| `kitesurf` | "Portable Bartender Barista **Kit**" |
| `wingsuit` | flying toy **wings**, a clothes-drying rack **wing**, a perfume, potted plants |
| `skydiving` | a real skydive **141.5 miles away in Devon**, and an online COSHH workplace-safety course |

**The matcher matches fragments, OR-ed together, with no relevance floor** — and every dashboard
behind it records a successful search. The API returns no relevance score, no matched-term field and
no spell-correction field, so the client genuinely cannot tell a real match from padding.

**That is why the supplied dataset's central limitation is not a weakness of the sample: it
reproduces what the platform actually exposes.**

## Two claims were withdrawn here, and they should stay visible

The brief grades whether claims survive checking, so the corrections are kept rather than tidied
away:

1. **"A word that matches nothing is completely inert"** — true for gibberish (`xqzjw massage` = 458,
   unchanged), false for real words: `paintball massage` returned 470 = 458 + 12 **exactly**, while
   `helicopter massage` returned **418, below `massage` alone**. Whatever the engine does, it is not
   a set union, and this run does not establish what it is. The surviving claim is narrower and
   worse for Groupon: **the user has no lever.** No word they add reliably narrows anything, so the
   system has no path to "we don't have that."
2. **A general two-word diacritic penalty** — it replicates to within 0.5pp for the `masaż` family
   (`masaż tajski` 162 vs `masaz tajski` 95) and **not at all** for three other Polish pairs, one of
   them also two-token. Effect is specific to one token family, not a general rule. F2's range in
   the supplied-data analysis was deliberately **left alone**, because widening it would import a
   live-catalogue result into a supplied-data measurement.

## What this folder does **not** establish

- Nothing about the supplied CSVs. Not one number.
- Scope actually run: GB (`london`) and PL (`warszawa`) only. DE / FR / ES hosts and the 18
  non-capital divisions are **unrun and parked** — no current claim depends on them.
