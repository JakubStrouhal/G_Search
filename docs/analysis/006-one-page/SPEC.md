---
created: 2026-08-06
updated: 2026-08-06
note: Build spec for the consolidated page — locks the sequence (data before narrative), the shell contract, the seven product screens with the four proposals cut against evidence, the generated manifest, the agent's grounding rules and the deployment surface.
---

# One page — build spec

Brief: `BRIEF.md`, decisions **G1–G6**. This spec covers **only what 006 adds**: the shell, the
manifest, the agent, deployment. The prototype itself is `001-part-b/SPEC.md` — referenced, not
restated. Where the two disagree, **001 wins on prototype behaviour and 006 wins on presentation**.

---

## 1. The sequence — locked, and this is the decision the unit turns on

> **Data first. Specifically: the threshold sweep first. The narrative wraps around what exists.**

Three facts settle it:

1. **The page is the delivery vehicle, not a deliverable.** The brief names three: Part A analysis
   (done), a **working clickable prototype** (zero lines), a two-page writeup (not started). If the
   page eats the prototype's hours, the package fails on the one requirement the brief states
   explicitly — *"a working, clickable prototype, not a deck."*
2. **The two halves are at wildly different maturity.** The narrative is ~80% done and every
   remaining task is execution: re-base onto design tokens, host it. The prototype is at zero and
   every hour there is discovery.
3. **Only §10 step 4 can invalidate the plan.** If the sweep cannot separate `absent` from
   `stocked`, then "failure classes behave visibly differently" — `001 SPEC` §1's top MUST — is not
   reachable, and seven styled sections would be built on it. Learn that before styling anything.

The failure modes are asymmetric, which is the tiebreak: **hosted narrative + no prototype = fails
the brief. Working prototype + a local explainer = still passes.**

### Order of work

| # | Step | Source | Gate |
|---|---|---|---|
| 1 | Migrations + seeds | `001 SPEC` §10.1 | — |
| 2 | Hand-write 75 service descriptions | §10.2 / **D2** — do **not** LLM-enrich | — |
| 3 | Offline embeddings → pgvector | §10.3 | — |
| 4 | **Threshold sweep, error rate reported both directions** | §6, §10.4 | **gates everything below** |
| 5 | Prototype screens by behaviour | §10.5 | 4 |
| 6 | Demand loop, staff panel, coverage table | §10.6–9 | 4 |
| 7 | **The shell** — sections 1, 2, 3, 5, 7 wrap around what exists | §3 below | 5 |
| 8 | **The agent** | §5 below | 7 |
| 9 | Deploy | §6 below | 8 |

**The agent is last because it is the most cuttable thing in the package.** That is a feature. If
hours run short, 1–7 and 9 still satisfy the brief; 8 is the one section that can be dropped without
a hole.

---

## 2. What step 4 must produce before any UI

Ground truth is the `coverage` column of `query_classes.csv` (751 rows), **not** `failure_class`:

| `coverage` | rows | correct behaviour |
|---|---|---|
| `absent` | **437** = F4 178 + F1 259 | fall below LOW → abstain |
| `plausible` + `stocked` | 314 | clear LOW |

`absent` is the spine's `nowhere` bucket. Calibrating on the 178 F4 rows alone would train the
threshold to abstain on supply voids while passing all **259 silent-substitution rows** — the exact
failure the prototype exists to fix. See `001 SPEC` §6, corrected 2026-08-06.

**Deliverable of step 4:** a committed sweep output with (HIGH, LOW), false-confident rate,
false-abstain rate, and the named failing pairs. It ships in the staff panel and in Part C. If no
(HIGH, LOW) separates the two sets, **stop and report that** rather than tuning to taste.

---

## 3. The shell

Single Vue 3 app. Sections are routes on one scrolling page with a sticky index.

| # | Section | Content | Data source |
|---|---|---|---|
| 1 | **The task** | Groupon's three asks, quoted, each with a link to where this package answers it | static copy — the only hand-written prose allowed to contain no numbers |
| 2 | **How we found it** | the two CSVs, the `market`+`city` join, row counts, **and what the data cannot answer** (no query→deal map, no relevance score, no sessions) | `FINDINGS.md` §0, §3 → `story_data.json` |
| 3 | **What is broken** | the four location buckets, then the language test, then the 52.5% cliff as support | `FINDINGS.md` §5f, §5b, §1 |
| 4 | **▶ The prototype** | live, clickable. Demo chips from `001 SPEC` §7. **The payload** | Supabase RPC |
| 5 | **What we built** | generated manifest — see §4 | `git ls-files` |
| 6 | **Ask the data** | the agent — see §5 | Edge Function |
| 7 | **The limits** | the honesty register, in full, unsoftened | `001 SPEC` §9 |
| — | **sidebar** | live production evidence, reachable from §2 and §7, **not a numbered section** | `story_data.json.live` |

### Rules that bind every section

- **G6 — no number is hand-typed into a component.** From `story_data.json` or a DB query, never a
  literal. `build_explainer.py`'s external-reference check carries forward into the build.
- **Bands are quoted as bands.** `nowhere` is **[43.2%, 64.7%]**, never one end. Enforce it in the
  formatter, not in review.
- **Contested figures never render.** `INDEX.md` #1 (adrenaline share of zeros), #6 (supply-void
  aggregate pair count), #7 (pair universe). Blocked at the data layer per G6, same as the agent.
- **G5 — design tokens.** `@design` alias off `docs/design/outputs/tokens.css` +
  `assets/prototype-theme.css`. **Declared twice** — `vite.config.ts` and `tsconfig.app.json`; edit
  both or it resolves in one and silently fails in the other. The explainer's own palette
  (`--paper`/`--ink`/`--oxide`) is replaced, not layered over.

### 3.1 The product, screen by screen — what a user actually sees

Shell section 4 in detail. **This is a specification of screens, not approval to build them** — step
4's sweep still gates every row, and the adjacency screen depends on the threshold separating
`absent` (437) from `stocked` (314). Behaviour is `001 SPEC` §3; this table is the same thing in
plain language, one row per thing a person can experience.

| # | User types | What they see | Class | The finding that licenses it |
|---|---|---|---|---|
| **S1** | `masaz tajski` (PL) — no diacritics | Real results, plus a visible line: **"we matched *masaż tajski*"** | F2 | §5b — English/stripped phrasing dead-ends 81.2% vs 39.0% local. The one layer that is genuinely fixable |
| **S2** | anything returning **1–2** results | **Near-empty state**, not a results page: "this is all we found, and it may not be what you meant" | result-count rule | §1 — 1–2 results converts at **1.7%** vs 16.1%, holding in 137 of 138 strata. A cliff, not a gradient |
| **S3** | `paintball` (GB) | **Abstention first**: "We have no paintball in London." **Then** labelled adjacency: "Not what you asked for, but nearby in Things To Do —" | F1 | §3 — zero paintball deals exist, yet median 9 results come back. The invisible failure |
| **S4** | `fallschirmspringen` (DE) | **Honest empty state.** "We don't have skydiving in Berlin. We'll tell you if that changes." → notify-me → **demand row written** | F4 | §5d — 178 pairs, 1,689 searches, zero every time. Search cannot fix supply at any quality |
| **S5** | staff view on S4 | Demand table → aggregated by market × city × concept → **mocked acquisition brief** | — | §5 — GB London 222 adrenaline searches, 0 deals. The loop closes on the supply side |
| **S6** | `manicura` (ES) | "Stocked in your city, and failing here far more than one city over — **we cannot say why**." No location claim | F3 | §5f — the diagnosis was withdrawn; the population was kept. Saying *unknown* is the honest screen |
| **S6a** | *(inside S6's staff panel)* | The cross-city rule **declining to fire**: `cross-city offer: SUPPRESSED — answering deal $89.57 (Manchester), below the $100 travel threshold` | F3 | The gate is real product logic; showing it **suppressed** is stronger than a screen that demos on a $102 manicure. Evidence in the cut table below |
| **S7** | any of the above | **Staff panel**: the matched document, the similarity, the band, the Part A class, the sweep's error rate | — | §1 — "show your working," the literal ask |

**The rule that binds S3 and S4, and it is the whole product:** *the abstention comes first, and the
alternative is labelled as an alternative.* A system that silently substitutes is the defect
(`FINDINGS.md` §3, and observed live — `kitesurf` → "Portable Bartender Barista **Kit**"). A system
that names what it could not match, then offers something else clearly marked as something else, is
the fix. **Knowing when to return nothing is the product requirement, not an edge case.**

#### Proposals evaluated and cut — recorded, not silently dropped

| Proposal | Verdict | Evidence |
|---|---|---|
| **"The answer is in another city — show the route, offer a taxi"** | **CUT as a screen; shipped as a *gate* — see S6a** | The whole market-wide another-city population is **145 dead ends (3.07%)**, composed of **hair 62 · karting 21 · gym 18 · personal trainer 17 · facial 13 · nails 10 · escape room 3 · city tour 1**. Nobody travels between cities for a haircut. `001 SPEC` §3 already withdrew this copy as false for **315 of 321** F3 rows |
| ↳ **"…but gate it on price — over \$100 it might be worth the trip"** | **Sound rule, and the catalogue cannot pay it off** | Tested against the exact `classify.py` `STOCK_TITLE` regexes: **generous** (≥1 answering deal over \$100) = **136 dead ends, 2.88%** of all 4,720; **strict** (median answering deal over \$100) = **18, 0.38%**. Composition is unchanged — the generous 136 are mostly \$100+ *hair packages and gym memberships*, and a gym one city away is worse than useless. **The reason price cannot rescue it:** the catalogue's ceiling is **\$179.46**, and the concepts where a high price *would* align with travel-worthiness — skydiving, helicopter, ballooning — have **zero deals**. The things worth travelling for are exactly the things this catalogue does not stock. **Right rule, wrong catalogue:** live Groupon stocks helicopter tours at 10–18 per city (`003-live-validation/RESULT.md` P3), so this ships in **Part C as a production recommendation with the threshold named**, not as a prototype screen |
| **"No helicopter? Offer a balloon ride instead"** | **CUT as stated; the intent survives as S3** | The catalogue contains **0** deals matching balloon / helicopter / skydive / parachute / paraglide / bungee — the L2 set is beauty, massage, dining, fitness, activities. Balloon is as absent as helicopter, so this swap is **the F1 bug shipped as a feature**. The intent is right and is S3's labelled adjacency: abstain first, then offer only what is actually stocked, always labelled |
| **"Log *who* searched"** | **CUT** | No user IDs, sessions or purchase history exist in `search_log.csv`. `001 SPEC` §1 cuts returning-customer features for the same reason: building it means fabricating evidence. The demand row is **`market · city · concept · query · date · count`** |
| **"Show the 13% of products we can serve"** | **Not a product surface** | **11.8%** (band 5.6–15.1%) is search's share of *recoverable purchases per month*, not a subset of the catalogue. It belongs in shell sections 3 and 7, never as a UI label |

---

## 4. The manifest (G3)

Generated at build time, never hand-typed — a path list drifts the way a figure drifts.

```
git ls-files 'docs/analysis/**/*.py' 'docs/analysis/**/*.js' 'supabase/migrations/*.sql'
```

Each row: path · one-line purpose · what it emits · last commit touching it (`git log -1`). Purposes
come from a committed `manifest.yml` keyed by path; **a path present in git and absent from the YAML
fails the build.** That is the check that keeps the manifest honest when a script is added later.

---

## 5. The agent (G4) — contract

This is the highest-risk component in the package. An unconstrained agent over this data will invent
the query→deal join, quote the contested figures, and state one end of the band — *the precise
failure the brief tests for, shipped as a feature.*

### Placement

Supabase **Edge Function**. Keys and model calls live there. The browser holds
`VITE_SUPABASE_PUBLISHABLE_KEY` and nothing else.

### Retrieval — a curated fact set, not the corpus

It answers from, and only from:

1. `story_data.json` — the computed figures, each already carrying its provenance
2. `FINDINGS.md`'s tagged statements — VERIFIED / INFERRED / CANNOT VERIFY, parsed with the tag
3. `query_classes` — per-pair lookup, the same table the prototype uses

**Not** the raw CSVs, **not** the repo, **not** the web.

### Hard blocks — at the retrieval layer, not in the prompt

A prompt instruction is a request; a retrieval filter is a guarantee. Blocked before the model sees
anything:

| Block | Why |
|---|---|
| the three contested figures | `INDEX.md` #1, #6, #7 — 004 routed around them; the agent must too |
| one-ended band quotes | the band is the claim |
| any live figure joined to a CSV claim, or the reverse | the catalogue-conflation trap, `FINDINGS.md` §5e |

### Output contract

Every answer carries a tag — **VERIFIED / INFERRED / CANNOT VERIFY** — and the artifact it came
from. An answer that cannot be tagged is not returned.

### It must refuse, and the refusals are specified

| Question | Required response |
|---|---|
| *"Which deals did query X return?"* | **CANNOT VERIFY** — `results_shown` is a count; there is no query→deal mapping |
| *"How many skydiving deals does Groupon really have?"* | out of scope — that is the live catalogue, and live sizes nothing |
| *"Which city should Groupon recruit merchants in?"* | the supplied data names cells; live cannot, and no vendor recommendation is licensed |
| *"Is 43.2% or 64.7% the real number?"* | both ends ship; the band is the answer |

**Build the refusals first and test them first.** They are worth more than the chat feature: *the
page's own agent abstains for the same reason the product abstains* is the strongest single line
available to Part C, and it is only true if the refusals actually fire.

### Evaluation, before it ships

A committed fixture of ~15 questions — the four above, plus answerable ones — with expected tag and
expected refusal. Run it in CI. **A refusal that stops firing is a regression, not a nicety.**

---

## 6. Deployment

| Layer | Where | Note |
|---|---|---|
| DB + Edge Function | Supabase, **remote project** | un-defers `005-stack-init` step 5 (remote link) and pending 4.4 |
| FE | Vercel | build is `vue-tsc -b && vite build`; type errors fail it |
| Secrets | Supabase only | browser gets the publishable key; **never** the legacy anon key, **never** the secret key |
| Data | seeded from `docs/brief/*.csv` via generated `docs/analysis/outputs/` | never hand-typed into a migration |

RLS on every table. The FE reads; **the only write path is `demand_events`**.

---

## 7. Honesty register — additions this unit owes Part C

Carried alongside `001 SPEC` §9, not replacing it:

1. **The page is a delivery vehicle.** It is not an additional deliverable and does not substitute
   for the prototype.
2. **Three approved decisions were reversed** — 004 E1, `001 SPEC` §1's visual-design cut, and the
   agent as new scope. Reversals are recorded in `BRIEF.md` G1–G6 with reasons, not smoothed away.
3. **The live-data boundary**, with the disclosure line in `BRIEF.md` and the live-probe hours on
   their own line.
4. **The sweep's error rate**, both directions, including the named failing pairs — whatever it says.
5. **The agent's refusal set is a designed feature**, and its evaluation fixture is committed.

---

## 8. Done looks like

1. One URL. Task → method → finding → **click the prototype** → manifest → ask the agent → limits.
2. Step 4's sweep output is committed and visible in the staff panel.
3. The prototype behaves differently per class, including abstaining on F4.
4. The agent refuses all four specified questions, tagged, in the shipped build.
5. Live evidence is reachable, labelled, and cannot be mistaken for an input to any figure.
6. No literal number in any component; the band never renders one-ended.
7. Hours logged, live probe on its own line.
