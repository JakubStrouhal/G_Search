---
created: 2026-08-07
updated: 2026-08-07
note: Codex refine findings applied — explicit state precedence with blank-input and error behaviour, v_demand_by_cell recut per source so "June" is implementable, live writes become server-only with notify_me the sole REST insert, and the side-by-side is labelled illustrative; 001 §2's unknown-query fallback marked superseded.
---

# The screens — spec

Approved to build 2026-08-07. Brief: `BRIEF.md` in this folder. Behaviour contract upstream:
`001-part-b/SPEC.md` §3 (wins on prototype behaviour) · presentation: `006-one-page/SPEC.md` §3.
**Every number below was re-run 2026-08-07 against the loaded local database** (`psql` on the local
stack; the remote lags by design and is the owner's write — `INDEX.md`).

## Thesis

**One page renders the five states the backend already computes — and the abstain state, 46.7% of
search volume, is the product, not the error page.**

## Scope — locked

| Priority | Component | Why |
|---|---|---|
| **MUST** | Five render states off one `search_deals` response: confident · adjacent · near-empty · abstain · refusal | Each maps to a branch the RPC actually returns. Verified today: abstain 46.7% / confident 32.4% / adjacent 20.9% of volume; near-empty 11.5% of 12,260 city×query combos; refusal fires for anything outside the 613 |
| **MUST** | Abstain-first + **labelled** alternatives | The binding rule of `001 SPEC` §3: name what was not matched, then offer only what is stocked, marked as an alternative. Silent substitution is the defect (F1) |
| **MUST** | Staff panel, toggle, default **open** | The literal "show your working" deliverable. Band + matched doc + similarity + thresholds + both error rates + Part A's class + the agreement flag + the **side-by-side** ("what today's system would have shown", real Groupon card treatment on the left, **labelled illustrative — never a claim about which deals a query returned**). Styled per §8.7: dark `#111827`, monospace scores, 420px slide-over, deliberately *not* Groupon — and "what the system does not know" set at equal visual weight to the scores |
| **MUST** | Demand disclosure + notify-me | Abstention already writes server-side; the UI must *show* it ("this gap was recorded — N searched this here in June") and offer the separate explicit signal |
| **MUST** | Market+city selector + curated chips + free text | Context before meaning; chips make every state reachable in one click; free text keeps the refusal honest and on display |
| **MUST** | **The Groupon design system** — `docs/design/DESIGN-SYSTEM.md`, tokens from `outputs/tokens.css` + `prototype-theme.css` via `@design` | Owner decision 2026-08-07, reversing the brief's "rough first" lean. §8 already designs exactly these screens: the three-band uncertainty grammar, purple-labelled adjacency, the near-empty inversion, the honest empty state answering Groupon's own zero-results screenshot, the dark unbranded staff panel |
| **MUST** | **A new page reached from the landing page — which is now the explainer.** Two doors, both to `/app#prototype`: the explainer's `#demo` section (the primary — its dashed "Open the prototype" button goes solid green, its status line rewritten), and the Part B card on `/app` | Owner decision 2026-08-07, re-pointed 2026-08-07 after the explainer became `/` (INDEX knock-on). The `#demo` door was *designed* to be this entry — "this button goes green when the status line above it is filled in" — and flipping it closes one of INDEX's two rot-flagged hand-maintained strings |
| **HIGH** | Coverage table section, always visible | `001 SPEC` §4 is a required deliverable; burying it loses the point |
| **HIGH** | Acquisition brief: aggregate table + one generated brief (GB · London · adrenaline) | Groupon's named growth driver; the loop closing on the supply side |
| **NICE** | Sticky section index | Navigation sugar on the one-page shell |
| **CUT** | **Cross-city travel/taxi offer as a screen** | Re-proposed 2026-08-07 and re-cut on a fresh run: at the proposed **€/£150** gate (data is `price_usd`, ceiling **$179.46**), **>$150 = 49 dead ends generous, 0 strict, of 4,720**. The concepts worth travelling for have zero deals. Survives only as the staff panel's **suppressed-gate line** (S6a) and a Part C production recommendation with the threshold named |
| **CUT** | A router dependency | `App.vue`'s one-hash pattern already exists (`#stack`) and its lazy-import discipline is load-bearing — `supabase.ts` throws at module scope on missing env, so the front door must never statically import anything that touches it |
| **CUT** | Anything §8 does not license: dark mode, invented brand assets, a fourth confidence device, red/warning for low confidence | The design system is extracted and tagged; inventing beyond its [I] set is the drift it exists to prevent |
| **CUT** | Any per-user feature, any "70 km" or distance copy | No sessions, no user IDs, **no geo data anywhere** — a kilometre figure would be invented |
| **CUT** | The agent (`006 SPEC` §5) | Separate unit, explicitly last and most cuttable in the 006 build order |

## Required behaviour

A new page at **`/app#prototype`** (hash route on the Vue app, lazy-loaded like `#stack`), reached
from the landing page — which is the **explainer** at `/`: its `#demo` section's "Open the
prototype" button becomes the live green door, and the Part B card on `/app` is the second one —
and **it does not inherit the landing page's case-study styling. It is built as a realistic Groupon
surface** (owner decision 2026-08-07): white header with the wordmark SVG as-is, the pill search
field with green ring and circular green submit (§5), a market/city selector chip beside it,
`Results for "X"` at 24px/800 with the right-aligned deal count that is present even at zero, deal
cards copied proportionally, sentence case throughout. The landing page is only the door; the
prototype is the shop.

Chips (secondary-button idiom) carry their own market+city and set the selector; free text stays
open. Every response renders exactly one state, each wearing its `DESIGN-SYSTEM.md` §8 device:

| State | Fires when | The user sees | §8 device | Verified trigger |
|---|---|---|---|---|
| **Confident** | `band=confident` | "Results for *X*" + deals. If `normalised=true`, a visible line: "we matched **{resolved_to}**" | Plain deal-card grid, unmodified — silence *is* the confident signal. Card copied verbatim (§5): 16:9 image, 8px radius, no border, no shadow | `masaz tajski` PL → confident, resolved to `masaż tajski`, 5 deals (ran today) |
| **Adjacent** | `band=adjacent` | **"We don't have *X* — closest stocked, which may not be what you meant:"** + deals, each with similarity | §8.4: grid inside a **purple-labelled container** (`#f5edfc` / `#d8b9f2`) — purple already means "this number has a caveat" on Groupon's own cards. Cards inside stay standard; the label does the work | `paseo en globo` ES·Madrid → adjacent, 6 deals |
| **Near-empty** | `near_empty=true` | "This is all we found, and it may not be what you meant" — not a results page. §1: 1–2 results convert at 1.7% vs 16.1% | §8.3, the inversion: **the abstention panel first, full width; the 1–2 real deals below it, unmodified.** Never a short grid | `escape room` GB·Birmingham → 1 available |
| **Abstain** | `band=abstain` | 1. "We don't stock *X* in {city} — and it isn't a search problem." 2. "**N searches** for this here in June" (`seed_searches` per cell — **never** the mixed total). 3. "This gap was just recorded." 4. Notify-me button. 5. **Labelled alternatives, floored at 0.30**: above it, "Closest things we *do* stock —" top 3 city-stocked services with similarity shown; **below it, suppressed** and replaced by "Nothing here is close to *X*. Here is what {city} does stock:" + category links | §8.5: Groupon's own empty-panel geometry, honestly worded — **never "try removing a filter"**. Notify-me is the **only green on the screen**. Demand confirmation per §8.6: teal-800 on `#e2f8fc`, one quiet line | `paintball` GB, `fallschirmspringen` DE, `manicura` ES — all abstain today |
| **Refusal** | `band=unknown_query` | The RPC's own `why`, verbatim: not in the logged 613, embeddings are precomputed, we will not guess. Presented as a designed card, not an error | Same §8.5 panel geometry, neutral — no red, no warning yellow: nothing has gone wrong | any unlogged string |

**The state contract, exhaustive and ordered** (Codex refine, 2026-08-07 — the RPC returns six
bands, not five, and `near_empty` is an independent flag):

- **Precedence:** `unknown_query` → refusal card · `empty` (blank input) → no state card, the input
  simply doesn't submit (disabled until non-empty; a forced blank POST renders nothing new) ·
  `abstain` → abstain state (`near_empty` is impossible there — `available` is 0 by construction) ·
  else `near_empty=true` **overrides** the band and renders the near-empty state · else the band
  renders. One state per response, deterministically.
- **Failure is its own honest state:** an RPC error or network failure renders an error card
  quoting the actual message — the config-missing branch *raises on purpose* rather than silently
  abstaining (`search_rpc.sql`), and the UI must not convert that into an empty state or an
  abstention. No retry theatre; the card names the failure.

**Customer motivation resolves to this and nothing more:** steering means chips that lead, and
alternatives that are (a) actually stocked in the city, (b) always labelled as alternatives, (c)
never presented as the answer. There is no query→deal mapping, so any stronger "lead them to the
right product" claim would fabricate relevance. Verified today the mechanism lands where `001 SPEC`
predicted: the top stocked alternative for `fallschirmspringen` (DE) **is karting** (0.18) — low
similarity, honestly displayed.

**The vendor loop resolves to S4 + S5:** the abstention write is automatic and server-side
(`source='live'`, verified `search_rpc.sql:159`); notify-me is a **second, explicit** signal
(`source='notify_me'`, new); the staff-side acquisition brief aggregates both by market × city ×
concept next to the seeded June baseline.

## What it does when it has no good answer

The graded requirement, and three different honest answers — never one generic empty state:

1. **Stocked nowhere in the market** (abstain): name the gap, show the June demand for it, record
   it, capture intent, offer labelled alternatives. Never "no results found".
2. **Almost nothing here** (near-empty): show the 1–2 deals under a warning frame, because
   rendering them as an ordinary results page is the invisible failure being rebuilt.
3. **Outside the logged world** (refusal): say exactly why nothing renders, by name. The refusal
   is the same honesty as abstention, applied to the demo's own limits.

The staff panel stays available in all three, showing the abstain/refusal reasoning and the
demand row just written.

## Architecture

- **One migration gates everything** (`supabase migration new screens_rpc_v2`, never editing
  applied ones):
  1. `search_deals` returns `alternatives`: top 3 services **stocked in `p_city`** by similarity,
     each `{title, category_l2, similarity, deal_count}` — computed always, rendered only below
     `confident`.
  2. `demand_events.source` check widens to `('seed','live','notify_me')` — today it is
     `('seed','live')` (verified `\d demand_events`), so **notify-me currently has no legal write
     path** — the one fact that makes this migration step 1.
  3. **The append policy flips to `source = 'notify_me' and n = 1` — not widens.** `search_deals`
     is `security definer`, so its `live` insert bypasses RLS; nothing else may write `live`. After
     this, an anon REST insert of `source='live'` **fails**, and a forged "system abstention" stops
     being possible (Codex P1: today anyone can inflate the brief over REST).
  4. **`v_demand_by_cell` is recut per source** — today it sums seed + live into one `searches`
     column, which makes "N searches in June" unimplementable. Replacement columns:
     `seed_searches` (sum of `n` where `source='seed'` — the June log, and the only number the
     abstain state's copy may cite), `live_abstentions` (row count), `notify_requests` (row
     count). No combined total ships; the brief displays the three separately.
- Everything else is FE-only: Vue 3, no router — the prototype is a **new hash route** on
  `App.vue`'s existing pattern (`#prototype`, lazy-imported exactly like `#stack`, because
  `supabase.ts` throws at module scope on missing env and the front door must render regardless).
  Two entry edits, one per door: (a) the explainer's `#demo` section — edited in
  `explainer.template.html` (the source; `outputs/` is generated by `build_explainer.py`, never
  hand-edited) — button from dashed to the solid green primary, `href="/app#prototype"`, and the
  `demo-status` line rewritten to state what is actually deployed; (b) the Part B card on `/app`'s
  `SiteIndex.vue` gains `href: '#prototype'` and a CTA in Part A's idiom. **Neither door flips
  until the screens are real — same change, same commit** — the door's own copy says an overstating
  demo undoes the page's honesty. The one hop that needs a deploy to prove stays `vercel.json`'s
  `/app` → `/app.html` rewrite (INDEX): `curl -I` it on the preview.
- Design source: `@design/outputs/tokens.css` + `@design/assets/prototype-theme.css` (the alias is
  declared twice — `vite.config.ts` and `tsconfig.app.json`; edit both or one silently breaks).
  `DESIGN-SYSTEM.md` §8's [I] surfaces are the design of record for the invented states; where a
  Groupon pattern exists (§5 deal card, pill search, chips), reuse it unmodified. The browser holds
  the publishable key; reads everywhere, writes only `demand_events`.
- **D1 stands:** the class rendered in the staff panel comes from `query_classes` via the RPC's
  `staff` block, never derived from the threshold.
- No number is a literal in a component (G6): thresholds and error rates from `search_config`,
  demand counts from `demand_events`, class facts from the `staff` block.

## Acceptance criteria

1. Every state reachable by a named chip: the 15 verified band chips (per market × band, e.g. GB
   `gym`/`indian restaurant`/`paintball`; DE `personal trainer`/`kart fahren`/`wildwasser
   rafting`) plus 5 near-empty chips (`kart fahren` Köln, `paseo en globo` Barcelona, `karting`
   Paris, `escape room` Birmingham, `masaż dla par` Kraków) — bands verified against local today.
2. `masaz tajski` (PL) shows the normalisation disclosure: `resolved_to = masaż tajski`,
   `normalised = true`.
3. `paintball` (GB · London): abstention copy first; **alternatives suppressed** (max sim 0.251 <
   0.30) with the "nothing here is close" copy instead; a `demand_events` row with `source='live'`
   visible in the staff panel after the search. `eyelash extensions` (GB · London, 0.396) shows the
   labelled block — **both branches of the floor are demonstrable**, and the staff panel names
   which fired and why.
4. Notify-me writes a `source='notify_me'` row over REST with the publishable key; an anon REST
   insert of `source='live'` **fails** (the policy flip holds); and the brief view shows
   `seed_searches` / `live_abstentions` / `notify_requests` as three numbers, never one total —
   so no demo click can inflate the June baseline.
4b. Blank input does not submit; killing the network (or an RPC error) renders the error card
   quoting the failure — never an empty state or an abstention. A query with `available` 1–2 in
   the confident band still renders near-empty (the precedence rule holds).
5. Staff panel shows: matched document + similarity, LOW 0.40 / HIGH 0.55, **both** error rates
   (false-confident 6.83% / false-abstain 23.22%, from `search_config`, never one alone), Part A
   class, coverage, and `band_agrees_with_part_a`.
6. **Both disagreement directions are demonstrable, not tuned away:** `manicura` ES → abstain vs
   Part A `stocked` (`agrees=false`, verified); `paseo en globo` ES → adjacent vs Part A `absent`
   — a live false-confident, shown as such.
7. `escape room` (GB · Birmingham) renders the near-empty state, not a results page.
8. An unlogged query renders the refusal card quoting the RPC's `why`; no results, no demand row.
9. The staff panel on `manicura` shows the S6a suppressed-gate line (cross-city offer: suppressed,
   with the reason), and no user-facing copy anywhere implies the answer is in another city.
10. Coverage table renders all rows of `001 SPEC` §4 including **F6 marked cut with its reason**.
11. Acquisition brief: top cell GB · London · adrenaline from `demand_events` aggregation; the
    lost-purchase figure computed at s2p 11.36% and labelled **upper bound**.
12. `grep -rE '43\.2|64\.7|46\.7|32\.4|20\.9|11\.5' web/app/src/` finds no hardcoded headline
    number in a component.
13. Both doors work: the explainer's `#demo` button (solid green, no longer dashed) and the `/app`
    Part B card both land on `/app#prototype`; the `demo-status` line no longer says "nothing to
    click yet"; `/app` still renders with no env configured (the lazy-import discipline holds).
    On the preview, `curl -I /app` proves the rewrite.
14. The `DESIGN-SYSTEM.md` §11 checklist passes, in particular: headings at **800**; green only on
    the primary CTA (notify-me on dead ends) and prices; purple only for adjacency; teal, not
    green, for the demand confirmation; the near-empty state renders panel-first, never a short
    grid; no empty state blames a filter; no text sits on `#9ea3ae` or `#e38e21`; German
    (`Fallschirmspringen`) and Polish (`masaż dla par`) strings checked at the narrowest card
    width.

## Honesty register

- **Alternatives are similarity-ranked titles, not measured relevance.** No query→deal mapping
  exists; the label and the visible similarity are what keep it honest. Carry into Part C.
- **Three demand signals, three meanings, never one number**: `seed` = the June log (the only
  source the word "searches" may describe); `live` = the system had nothing (server-only, fires
  with or without a UI); `notify_me` = **button presses, not people** — no sessions or user IDs
  exist, so duplicates cannot be deduplicated and no copy may say "N people".
- **The staff side-by-side is illustrative, never historical.** "What today's system would have
  shown" renders a Groupon-style page of that city's catalogue as a treatment comparison — there
  is no query→deal mapping, so it must carry the label *"illustrative — the log records a count,
  not which deals"* and may never present specific deals as what a June query returned.
- **Refusals write no demand row** — an unlogged query has no concept to attribute. Say so in the
  staff panel rather than letting the brief silently under-count.
- **The band and Part A disagree in both directions** and the demo shows one of each (criterion 6).
- **The chips are curated** — chosen today from verified bands. Free text stays open precisely so
  the demo is not only its happy paths.
- **The cross-city rule is sound and this catalogue cannot pay it off** (49 generous / 0 strict at
  >$150; ceiling $179.46) — a Part C production recommendation, never a screen.
- **The page deliberately reads as Groupon** — wordmark, tokens, card proportions — inside a
  case-study deliverable only (`DESIGN-SYSTEM.md` §1's trademark note). Every divergence from the
  real site is one of §8's tagged [I] inventions, each an argument about search behaviour, not a
  taste preference. Placeholder imagery stays visibly placeholder (`#edeff2`), no fabricated
  merchant photos or reviews.
- **Everything verified here is verified against local.** The remote carries the old seed and lacks
  migration 3; nothing a grader clicks is proven until the owner pushes and the deploy is re-probed.

## What would make this spec wrong

- If the new `alternatives` computation cannot keep "stocked in this city" true on reseed, the
  abstain state loses its third block — criterion 3 would catch it.
- If any chip's band moves after a `db reset` (it should not — embeddings are deterministic), the
  chip set is re-derived from the same SQL, committed in the seed pipeline, not hand-edited.

## Build order

1. **The migration** (`alternatives` + `notify_me` source/policy). Verify by `psql`: paintball GB
   returns 3 city-stocked alternatives; a `notify_me` insert passes RLS with the anon key; a
   `source='x'` insert fails. Gates every screen.
2. The page frame as a realistic Groupon surface: `#prototype` hash route + lazy import, landing
   card link, header (wordmark, pill search, selector), tokens + `prototype-theme.css` wired.
   Chips committed as a generated fixture from the band SQL; RPC wiring.
3. The five render states, ugliest-first: abstain → refusal → near-empty → adjacent → confident —
   each with its §8 device, deal card copied verbatim once and reused.
4. Staff panel per §8.7 (dark, monospace, slide-over), incl. the disagreement flag, the S6a
   suppressed-gate line, and the side-by-side against the real Groupon card.
5. Notify-me write + demand-count display + "row just written" view.
6. Coverage table section.
7. Acquisition brief section (aggregate + one brief, computed).
8. **Flip the doors, last and in the same change that makes them true:** explainer template's
   `#demo` button → green + `/app#prototype`, `demo-status` rewritten, regenerate via
   `build_explainer.py`; `/app` Part B card gains its CTA.
9. Run the demo script end to end (the five `001 SPEC` §7 queries + `paseo en globo` + one
   refusal); log hours.

## Decision log

| # | Question (brief §5) | Resolution | Why |
|---|---|---|---|
| 1 | Seven screens or four states? | **Five render states, one search section** — the brief's four plus the refusal, which is real and 613-bounded | Each state is a branch the RPC returns; a screen with no code branch is theatre. S1/S6 are one component with different `staff` content |
| 2 | One page or routes? | **REVISED by owner 2026-08-07: the prototype is its own page**, a `#prototype` hash route lazy-loaded off `App.vue`'s existing pattern, clicked through from the landing page's Part B card | Owner instruction. No router dependency — the `#stack` pattern and its load-bearing lazy import already exist. 006 §3's one-page shell remains the later consolidation vehicle; this page becomes its section 4 |
| 3 | Free text or chips? | **Both; chips lead, refusal shown proudly** | Chips make all states reachable in one click; the refusal card is the honesty requirement applied to the demo itself |
| 4 | Who picks market+city? | **Persistent selector, all 20, default GB·London; chips override** | The data is loaded for all 20 at zero marginal cost; chips remove the navigation burden |
| 5 | Staff panel mode | **Toggle, default open** | Highest-value component for this audience; hiding it by default hides the deliverable |
| 6 | Near-empty own state? | **Yes** | 11.5% of combos, verified today; rendering it as a results page rebuilds the invisible failure |
| 7 | Acquisition brief depth | **Aggregate table + one computed brief (GB·London·adrenaline)** | Maps to the named growth driver; one brief proves the loop, five would prove hours |
| 8 | Coverage table placement | **Always-visible section** | Required deliverable; a grader checks for the unfixable rows in ten seconds |
| 9 | Design agent output or rough? | **REVISED by owner 2026-08-07: follow `DESIGN-SYSTEM.md` and build it as a true, realistic Groupon surface** — reuse §5 patterns verbatim, take §8's [I] designs as the design of record, pass the §11 checklist. Not limited by the landing page's minimal styling | Owner instruction, twice stated ("follow the design system", "make it true realistic"). The system is extracted and tagged, so this is assembly, not invention — and §8 *is* the analysis rendered as design: the uncertainty grammar is the argument |
| 10 | Notify-me, given auto-write? | **Yes, separate `notify_me` source — needs the step-1 migration** | "We had nothing" and "tell me" are different facts; today the constraint+policy make the second illegal to write |
| 11 | Adjacency on abstain (unknowns #1) | **Extend the RPC with `alternatives`, city-stocked, labelled** | 001 §3 F4 requires it; the current RPC returns `[]` on abstain, so FE-only cannot deliver it honestly |
| 12 | Customer motivation (owner ask) | **Chips + labelled stocked alternatives, nothing stronger** | No query→deal mapping — any stronger steering claim fabricates relevance, the exact graded failure |
| 13 | Cross-city taxi at €150 + two tickets (owner ask) | **Cut as a screen; S6a suppressed line + Part C recommendation** | Re-run today: >$150 = 49/0 of 4,720; no geo data for "70 km"; no basket data for "two tickets"; currency isn't in the data |
| 14 | Which door, now the explainer is `/`? (INDEX knock-on) | **Both: the explainer's `#demo` door is primary, the `/app` Part B card secondary — one destination, `/app#prototype`. Doors flip in the same change that ships the screens, never before** | The `#demo` section was designed as this exact entry ("goes green when the status line is filled in"), and flipping it closes one of INDEX's two rot-flagged hand-maintained strings |
| 15 | Are five states exhaustive? (Codex P0) | **No — six bands plus a flag. Precedence rule added: refusal · blank-doesn't-submit · abstain · near-empty overrides · band. Errors get their own card** | The RPC returns `empty`, and `near_empty` can co-occur with confident/adjacent; without precedence the rendering contract is untestable |
| 16 | Can the UI say "N searched in June"? (Codex P0/P1) | **Only after the migration recuts `v_demand_by_cell` per source; `live` becomes server-only (RLS flip, not widening); notify-me counts button presses, never people** | Today's view sums seed+live into one number, so a demo click would silently join the June log; anon can forge `live` rows over REST |
| 17 | The side-by-side vs the no-mapping rule (Codex P1) | **Labelled illustrative, always** — a treatment comparison, never "these are the deals the query returned" | `results_shown` is a count; presenting specific deals as the historical result would be the exact fabrication the analysis refuses |
| 19 | `available = 0` outside the abstain band — a state the five-row table missed (found in build, 2026-08-07) | **A sixth state, `city_empty`.** RPC flag `available = 0 and band <> 'abstain'`; renders abstain-shaped with **no `Results for` heading**, copy "Nothing in {city} matches *X*", **no** "isn't a search problem" line, **no cross-city claim in any form**, notify-me primary, alternatives floored as usual. Staff panel carries `market_max_similarity` beside `available` 0. Writes its own `source='city_empty'` demand row | **424 combos** (92 confident + 332 adjacent) rendered as `Results for "X"` over an empty grid — Groupon's own zero-results screen, the artifact this build answers. Verified: 424 flagged, 1,410 near-empty, **zero overlap**; `limpieza facial` ES·Valencia is band `confident` at market sim **0.7552** with 0 city deals. `near_empty` was **not** widened to 0–2: the 1–2 boundary carries §1's conversion cliff, and a state named "near-empty" firing on zero is a lie in a variable name. Source kept separate from `live` because the brief renders that column as "abstentions" — a distribution gap is not a semantic gap, and they have different owners |
| 18 | Alternatives with no plausible alternative (owner, 2026-08-07) | **Similarity floor 0.30. Above it, top 3 labelled; below it, suppressed for "nothing here is close" + category links** | GB London's closest stocked thing to `paintball` is a **manicure** (0.251) — honest but absurd. Verified against local: the floor splits 419 abstain pairs **186 show / 233 suppress**, and it splits them *meaningfully* — adrenaline suppresses (skydiving 0.215, rafting 0.179), `eyelash extensions` GB shows beauty at 0.396. **Deviates from `001 SPEC` §3 F4 step 3** ("closest thrill we do stock: karting"), which is exactly the case the floor kills: karting is not a thrill substitute at 0.18 |
