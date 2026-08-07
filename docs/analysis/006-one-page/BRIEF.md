---
created: 2026-08-06
updated: 2026-08-06
note: Opens the consolidation unit — one deployed page carrying task, method, findings, the live prototype and a grounded data agent; records the three spec reversals it depends on.
---

# One page — the task, the method, the prototype, the limits, deployed

Opened 2026-08-06. **Plan only — nothing below has been executed.**

## The question

Part A has a readable artifact (`004-data-story/outputs/explainer.html`, a local file). Part B has
an approved spec and an empty stack. Part C has nothing. Three deliverables, three surfaces, none
of them published.

This unit asks for **one deployed page** — Supabase + Vercel — that a grader opens from a link and
reads top to bottom: what Groupon asked, how we got the data, what is broken, **the working
prototype**, what we built, and where it stops being true.

## The decision that determines whether this works

> **Does the page *contain* a working prototype, or *describe* one?**

The brief requires "a working, clickable prototype, not a deck," handling every query type
**including the ones that cannot be fixed**. `supabase/` currently has **zero migrations and zero
tables**.

**Decided: the narrative is the shell; the live prototype is a first-class section inside it** —
not an appendix, not a screenshot. If the shell gets built first and the prototype "later", this
ships as a very polished deck and fails the brief's central requirement.

**Consequence for build order: nothing visual until `001-part-b/SPEC.md` §10 step 4 exists.** The
threshold sweep gates all UI, and it gates it *harder* here — if the whole site is styled around
class-specific behaviours and the thresholds then fail to separate the classes, the page's central
claim breaks with it.

## Page spine

| # | Section | Source |
|---|---|---|
| 1 | **The task** — what Groupon asked, in their words | `docs/brief/*.pdf` |
| 2 | **How we found it** — the two CSVs, the join, what the data cannot answer | `FINDINGS.md` §0, §3 |
| 3 | **What is broken** — the four location buckets, then the language test | `FINDINGS.md` §5f, §5b; 004 chapters |
| 4 | **▶ The prototype** — live, clickable, per-class behaviour · **the payload** | `001-part-b/SPEC.md` §3, §7 |
| 5 | **What we built** — manifest of scripts and notebooks | generated, see G3 |
| 6 | **Ask the data** — the grounded agent | see G4 |
| 7 | **The limits, stated** | `SPEC.md` §9 honesty register |
| — | *sidebar, off the main path* | **live production evidence** (see G2) |

## Decisions taken in this unit

| # | Question | Decision | Consequence |
|---|---|---|---|
| **G1** | One deployment or two? | **One.** Narrative shell + live prototype + agent, single Vercel app against a single Supabase project. | Reverses `004/BRIEF.md` **E1** ("beside Part B, not part of it"). 004's hours stay logged separately; they are still additive and still get reported as such. |
| **G2** | Where does live production evidence sit? | **Sidebar off the main path, not a numbered chapter.** | See "The live-data question" below. Reverses nothing in substance — the firewall and the visual separation are unchanged — but removes the reading that live is a co-equal input. |
| **G3** | The file manifest | **Generated from the repo** (`git ls-files` over `docs/analysis/**/*.py` + the notebooks), never hand-typed. | Same rule as numbers. A hand-typed path list drifts exactly the way a hand-typed figure does. |
| **G4** | The data agent | **Build it, grounded and able to refuse.** Rules below. | New scope, in no existing spec. It is the single highest-risk component in the package. |
| **G5** | Visual design | **Match `docs/design`.** | Reverses `001-part-b/SPEC.md` **§1** ("make it look like Groupon" — CUT, visual design not assessed). Real cost, stated: the explainer carries its own editorial palette (`--paper`/`--ink`/`--oxide`) and **zero** Groupon tokens, so this is a re-base onto `tokens.css` + `prototype-theme.css`, not a config flip. The `@design` alias is declared **twice** — `vite.config.ts` and `tsconfig.app.json`; edit both or it silently resolves in one. |
| **G6** | Numbers in the page | **No number is hand-typed into a component.** From `story_data.json` or the DB, never a literal. | Carries forward `build_explainer.py`'s guard, which is the repo's defence against the 11.5 → 11.4 → 299 failure mode. Whatever replaces that build step must keep the check. |

## The live-data question — settled here

The brief asks for analysis **of the supplied CSVs**. A grader who sees production Groupon data in
the package may reasonably ask whether the assignment was done. The position:

> **The analysis is the CSVs, end to end. Every number that sizes anything traces to them. Live is
> not an input to any figure — it is evidence about the platform, which Part C separately asks for.**

**The one dependency that existed has been removed** (2026-08-06, this unit). `002-recoverability`
attributed F5's withdrawal to live probe P4, which made the **~12% headline depend on the live
catalogue**. It no longer does: the 40% was an inference *from an absence* with a competing
explanation the supplied data cannot rule out, and an unattributable inference does not license a
point estimate. Withdrawn on CSV grounds; live corroborates. **The number does not move** — F5 is
(0,0,0) either way, central estimate 36 purchases/mo, 11.8%, band 5.6–15.1%, re-run and confirmed.

Two things stay separate, permanently:

- *"We cannot attribute the missing 3s, so F5's recoverability is withdrawn"* → **CSV-only**
- *"The missing 3s are a generator artifact"* → **live-tagged** (`FINDINGS.md` §1 item 2)

Withdrawing a claim needs no live evidence. Asserting a cause does.

**Why live stays in the package at all** — two named brief requirements the CSVs structurally
cannot serve:

1. **"What the platform teams who own search globally must supply."** The CSVs say nothing about
   what Groupon's search platform exposes. `BrowseDealFeed` returns no relevance score, no
   matched-term field, no spell-correction field. That turns a generic ask into *expose match
   provenance*, naming real fields in a real response.
2. **"What the AI tools got wrong that had to be caught."** The inert-word claim falsified, the
   diacritic penalty failing to generalise, the London-only "stocks adrenaline abundantly"
   correction. The best material in the package for a required deliverable.

**The release valve that makes G2 free:** chapter 2's load-bearing claim — *two results is not the
same as "we found it"* — is **already proven from the CSVs** (the 1–2 band converts at 1.7% vs
16.1%, `FINDINGS.md` §1). Live makes it vivid; the argument does not need it. So the placement is a
presentation call with nothing at stake in the analysis.

**Disclosure line, for Part C, verbatim:**

> The analysis is the supplied CSVs, end to end — every number traces to them. We additionally ran
> ~45 minutes of public, read-only searches on Groupon's own site (no account, no writes, script
> committed as `live_probe.js`). Not to source numbers, but because the brief asks what the platform
> teams must supply, and that ask should name real fields in a real response.

**Log the live-probe hours as a separate line.** Output-per-hour is graded; burying them inside
"Part A analysis" muddies both figures.

## The agent — grounding rules, locked before any code

An unconstrained chat agent over this data will confidently answer questions the data **cannot**
answer. It will invent the query→deal join. It will quote the contested figures 004 deliberately
routed around (`INDEX.md` #1, #6, #7). It will state one end of the `[43.2%, 64.7%]` band. That is
precisely the failure the brief tests for, shipped as a feature.

1. **Model calls in a Supabase Edge Function, never the browser.** The browser gets
   `VITE_SUPABASE_PUBLISHABLE_KEY` and nothing else.
2. **Grounded, not free-roaming.** It answers from a curated fact set — `story_data.json` +
   `FINDINGS.md`'s tagged statements + `query_classes` — not from the raw CSVs and not from the repo.
3. **Every answer carries the taxonomy**: VERIFIED / INFERRED / CANNOT VERIFY.
4. **It must be able to refuse.** *"Which deals did query X return?"* → CANNOT VERIFY, there is no
   query→deal mapping. *"How many skydiving deals does Groupon have?"* → that is the live catalogue,
   we cannot size it. Build the refusal deliberately and it becomes the strongest line in Part C:
   **the page's own agent abstains for the same reason the product abstains.**
5. **Blocks at the retrieval layer, not in the prompt** — contested figures, one-ended band quotes,
   and any live-figure/CSV-claim crossing.

## Build order — `001-part-b/SPEC.md` §10, unchanged

1. Migrations + seeds: `deals`, `deal_documents`, `query_classes`, `demand_events`
2. **Hand-write the 75 service descriptions** — do not LLM-enrich (D2); enrichment collapses F4 into
   F1 and makes the central finding an artifact of generated text
3. Offline embeddings → pgvector
4. **Threshold sweep against Part A's labelled pairs; report the error rate.** Nothing visual first
5. Prototype screens by behaviour + the narrative shell around them
6. Demand loop, staff panel, coverage table
7. The agent
8. Deploy — un-defers `005-stack-init` step 5 (remote link) and pending 4.4

## Out of scope — stated, not deferred

- **Re-running any Part A analysis.** The numbers are settled; this unit presents and deploys them.
- **Reconciling the two `CONCEPTS` maps** or closing `INDEX.md` #1/#2/#6/#7. Routed around, as 004 did.
- **New live probing.** What exists is enough for the two requirements it serves.

## Done looks like

1. One URL. A grader reads the task, the method, the finding, **clicks the prototype**, sees the
   manifest, asks the agent a question, and reads the limits.
2. Every number on the page traces to `story_data.json` or the DB. No literals in components.
3. The prototype behaves **differently per class**, including refusing on F4.
4. The agent refuses at least one question it cannot answer, visibly and with the reason.
5. Live evidence is reachable, labelled, and impossible to mistake for an input to any figure.
6. Real hours logged, with the live probe on its own line.
