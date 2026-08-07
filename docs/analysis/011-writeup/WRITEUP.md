---
created: 2026-08-07
updated: 2026-08-08
note: Part C, the two-page writeup plus the log. Canonical source — the /app#writeup page renders outputs/writeup.json, generated from this file; nothing is retyped into a component. check_writeup.py fails the build if any figure here stops resolving to the data.
---

# Part C — Groupon international discovery

*Two pages. Part A is the explainer at `/`; Part B is the prototype at `/app#prototype`. Every
figure below regenerates from a committed script — `check_writeup.py` fails if one drifts.*

## What we found

One month, **8,997** searches across five markets and twenty cities, against a **568**-deal
catalogue. First, the limit that shapes everything after it: the log records `results_shown` as a
**count**. There is no query→deal mapping and no relevance score, so any statement about *which*
deals a query returned is inference from the catalogue, not observation. We did not engineer around
that.

**The number a dashboard would show is the wrong number.** 29.3% of searches return zero results —
but a search returning 1–2 results converts like one returning nothing: **1.7%** search→purchase
against **16.1%** at four or more. That is a cliff, not a gradient. The real dead-end rate is
**52.5%**. It survives the obvious objection that 1–2 might simply attract worse queries: compared
*within* 138 concept × city strata, search→purchase moves by 0.02pp and the direction holds in
**137 of 138**. The metric is a property of the result count, not of which queries land there.

**Re-asking "why did it fail" as "where was the answer" is what assigns an owner.** Over all
**4,720** dead ends:

| Where the answer was | Dead ends | Share | Owner |
|---|---|---|---|
| Nowhere in the market | 2,039 | 43.2% | Merchant acquisition — not search |
| The user's own city | 1,520 | 32.2% | Search |
| Another city in the market | 145 | 3.1% | Product / UX |
| Can't tell from this catalogue | 1,016 | 21.5% | Not attributed |

One judgement moves the top row — whether a generic deal counts as an answer to a specific query.
Across the three defensible conventions the *nowhere* share runs **[43.2%, 64.7%]**, and under one
of them same-city overtakes it. We publish the band, never an end of it. Its hard core is **178**
market+query pairs / **1,689** searches that returned zero *every single time* — the definition the
prototype acts on, chosen over the analysis script's slightly wider rule (185 / 1,691) so the
writeup and the working thing cannot disagree.

**Phrasing costs far more than spelling does.** On matched pairs — same concept, same market,
restricted to concepts the catalogue stocks — English phrasing dead-ends **81.2%** of the time
against **39.0%** for local phrasing. A **42.3pp** gap, 47 of 48 pairs pointing the same way,
holding in all four non-English markets. Both confounds are killed: loanwords naming unstocked
concepts fail at the ordinary 44.0%, so this is not supply; rare *local* queries fail at 53.3%, so
it is not rarity. Typos, by contrast, are worth about **1.9%** of zero-result searches on the strict
definition — the matcher is already fuzzy on spelling.

**Most of this is not a search problem, and the honest number is the uncomfortable one.** Of the
1,520 same-city failures, a named mechanism exists for 355; the other **1,165** are stocked,
failing, and unexplained. Search-side work is worth roughly **12%** of the recoverable
opportunity — about **36** purchases a month against a base of **723** — while the supply-void
ceiling is **+271**. Two tighter readings give 7.8% and 5.7%. We publish the most generous and say
the other two exist.

## What we built, and why that rather than the alternatives

The prototype **abstains before it substitutes**. Silent substitution is the defect, not the
fallback: probed live, `kitesurf` on Groupon returns a *Portable Bartender Barista **Kit***. The
matcher matches fragments, and the production API exposes no relevance score, no matched-term field
and no spell-correction field — so the client cannot tell a real match from padding. Naming what
could not be matched, then offering something explicitly *labelled* as an alternative, is the fix.

Six render states, each a branch the backend genuinely returns: confident; adjacent, labelled and
with the similarity shown; near-empty, where 1–2 results get a panel rather than a results page;
nothing-in-this-city; abstain, which names the gap, shows the June demand for it, records the gap
and captures intent; and a refusal for anything outside the logged 613. Abstention is the product,
not the error page.

What we did not build, each cut with a number rather than an opinion:

- **"The answer is in another city — offer the trip."** The whole population is 145 dead ends: hair
  62, karting 21, gym 18, nails 10. Nobody travels between cities for a haircut.
- **"Then gate it on price — over $100 the trip is worth it."** Sound rule, wrong catalogue: 2.88%
  generous, 0.38% strict. The ceiling is $179.46 and the concepts worth travelling for have zero
  deals. It ships as a production recommendation with the threshold named, not as a screen.
- **"No helicopter? Offer a balloon."** Balloon is equally absent. That swap ships the
  silent-substitution bug as a feature.
- **Embeddings from a hosted model API.** Nobody can re-run an API pipeline without their own key,
  so the central claim stops being checkable. 75 service documents and 613 query vectors come from
  a local model and are committed.
- **A second retrieval system.** pgvector inside the same Postgres; at 568 deals an index would be
  theatre.

The threshold is calibrated against Part A's own labels rather than tuned by eye: **AUC 0.805**
across 751 pairs, **0.934** on the 147 the analysis is confident about, which carry 90.1% of search
volume. The upper band is a judgement and we say so — nothing in this data labels
confident-versus-adjacent.

## What we would do next, and what we need from the platform teams

**Week one is instrumentation, because most of what we would want is not recorded anywhere.** In
priority order the platform ask is: **query→results mapping with a relevance label**; null-result
events carrying the raw query; session IDs and timestamps; ranker scores with impression positions.
Without the first, every claim about which deals answered a query stays inference — ours included.

Then: make a discriminating term actually *constrain* the result set, and audit the expansion stage
— adding `helicopter` to `massage` currently *reduces* the count, so whatever is happening is not
union semantics and is not visible from outside. Fix the autocomplete service, which returned
`INTERNAL_SERVER_ERROR` on most probes across two hosts and two days; that is the layer where spell
correction and query understanding live. And route the supply-void bucket to merchant acquisition,
using the demand rows the prototype already writes as its input.

## How we would measure it, and what would tell us it was not working

**Primary metric: dead-end rate at two results or fewer, replacing zero-result rate.** Baseline
52.5%. The swap *is* the finding; reporting the old metric hides nearly half the problem.

**Read it only as a pair with the guardrail.** At the shipped threshold the system is wrong in two
directions — **6.83%** false-confident and **23.22%** false-abstain by search volume. Different
mistakes, different owners; one blended accuracy number hides which is being made.

**The counter-signal is the one to watch, and it is nth-order.** Loosening the matcher lowers the
dead-end rate *and makes the invisible failure worse*. A dead-end improvement arriving alongside a
rising false-confident rate is not an improvement — it is the silent-substitution defect being
manufactured. A headline win only counts if the guardrail held.

**What would tell us it was not working:** abstain-path sessions not converting above the 1.7%
near-empty baseline; labelled alternatives earning clicks but not purchases, which is substitution
accepted and then regretted; demand rows concentrating in concepts acquisition cannot act on. And
the ceiling — the ~12% is an upper bound on what a search fix delivers, not a forecast. Recovered
demand converts worse than organic demand.

**None of it is measurable on the supplied data** — no session IDs, no order values, no
reformulations. These are production instrumentation asks, and saying so is the point rather than
the caveat.

*Two limits, plainly. The data is clean enough to be synthetic, so the language test shows the
generator encoded a language effect — evidence the thesis is coherent and quantifiable, not proof
about production. And the live probe is a different catalogue: it shows how a real search engine
fails and sizes nothing. Live Groupon does stock paintball and sushi in GB; the void is this
catalogue's.*

## The log

**Hours: 8:01** of owner wall-clock, tracked. Machine time is recorded separately in each unit's
`RESULT.md` and is deliberately **not** added to it — roughly 0.6 h for the access gate and 1h50m
of agent execution across two build lanes for the screens. Adding the two would inflate the exact
number this exercise grades output against.

**Tools.** Claude Code (Opus/Fable 5) as the lead throughout: analysis scripts, the schema and RPC,
the front end, and the writing. For the screens it dispatched a three-role agent team — a backend
builder, a front-end builder and a read-only reviewer — with separate write scopes. **Codex** ran
as an independent, read-only conformance interviewer at two fixed moments: before a spec was
approved, and when an implementation claimed to be finished. A Claude design pass produced the
explainer's visual comp. Embeddings are a local `sentence-transformers` model; **no API key exists
anywhere in this repo.**

**What the tools got wrong, and had to be caught.** Three worth naming. **(1)** The analysis script
confidently printed `MATCHER FAILURE` for adrenaline — the exact opposite of the truth — because
the stock test ran at category level, where five categories make everything look stocked. Re-running
it at *title* level inverted the headline to a supply void. **(2)** A live probe concluded London
"stocks adrenaline abundantly" from multi-word result counts that were inflated by the very
fragment-matching defect the same paragraph was describing; only probing Berlin and Paris with
single tokens exposed it, and one probe had contradicted another inside the same session.
**(3)** A cross-lingual acceptance check passed on nothing — it hard-coded three query strings
absent from the log, so every case silently skipped and the criterion went green.

The pattern across twelve recorded retractions is one thing: **a coarse or convenient measurement
mistaken for a finding.** Every one was caught by measuring the same thing a second way, never by
re-reading the first result. Our own concept map carries the same class of defect it diagnoses in
Groupon's search — its `gym` pattern matches the English title and not the four local-language
equivalents. It changes no published number, which is exactly why it is easy to miss.
