---
created: 2026-08-07
updated: 2026-08-07
note: Handoff brief for redesigning outputs/explainer.html onto Groupon's design system — carries the three build gates that break a naive redesign, the register decision (R1–R4), the full component inventory, and the data-slot contract that keeps numbers out of the comps.
---

# Redesign brief — `outputs/explainer.html` onto Groupon's design system

**Hand this whole file to the design agent.** It is written to be self-contained: everything needed
to produce an implementable design is here, with file pointers for depth.

**One line:** the page is a *forensic report about Groupon's search*, currently set in a
paper-and-ink editorial style that has nothing to do with Groupon. Rebuild it in Groupon's own
design system — its type, palette, shape and spacing — **without** letting it become a fake Groupon
product page.

---

## 0. Read this before anything else — three build gates

The page is not hand-written HTML. It is `explainer.template.html` (81 KB, 362 lines of CSS, one
`<script>`) pushed through `build_explainer.py`, which enforces three things. **A design that
violates any of them is not implementable.**

### Gate 1 — no external references, at all

`build_explainer.py:44` aborts the build if the output contains `http://`, `https://`, `cdn.`, or
**`<link `**. Three literals are exempt (pinned probe URLs quoted as evidence, and the two XML
namespace strings `createElementNS` requires).

Consequences, and they are not negotiable:

- **Google Fonts `<link>` cannot be used** — even though `DESIGN-SYSTEM.md` §3 prescribes it. Fonts
  must be inlined as base64 `@font-face` data URIs inside the existing `<style>` block. §5 below has
  the measured plan.
- **`@import './tokens.css'` cannot be used** — even though `006-one-page/SPEC.md` §3 (G5)
  prescribes it for the Vue app. The explainer needs a **curated inline `:root` block**, not the
  335-line generated file.
- No remote images, no icon CDN, no analytics. The page must open from `file://` on a laptop with
  the wifi off. That property is part of the deliverable.

### Gate 2 — the drift guard: no number may be typed into the page

After building, the script scans the prose region (everything between `</style>` and `<script`) for
digit runs and fails on anything outside this allow-list:

```
ALLOWED_NUMERIC = {"1", "2", "3", "4", "5", "1–2", "4+", "0%", "29944"}
FORBIDDEN_WORDS = ("thousand", "hundred", "ninety", "percentage point", "per cent")
```

So **no mockup may contain a real figure as typed text**. Every number arrives at runtime through
one `__STORY_DATA__` token (there must be exactly one) bound to an element `id`. A comp showing
"43.2%" as a headline is fine as a *picture of intent*; the delivered template must carry
`<span id="bk-nowhere-lo"></span>`. §8 lists the data slots that exist.

*Why:* the repo's recurring defect is a stale figure surviving inside a derived one. Six hand-typed
numbers had accumulated by 2026-08-06 before this was made a build failure rather than a
convention.

### Gate 3 — every chart is runtime inline SVG

All five figures are drawn into empty `<svg>` nodes by JS from `story_data.json` on load, share one
set of drawing helpers, and are hover-bound to a single floating tooltip node. **No PNGs, no static
SVG with baked values, no chart library.** A design deliverable for a figure is: layout, palette
roles, axis/label treatment, hover behaviour — not a rendered chart.

---

## 1. Decisions taken, with the rejected alternative named

These are settled. They are recorded here rather than left for the design agent to resolve by
accident.

### R1 — Groupon's design *system*, applied to a report. Not a Groupon product surface.

`DESIGN-SYSTEM.md` §1 forbids the alternative outright: the wordmark and assets must not go on
"anything that reads as a real Groupon product surface." So the page adopts Nunito Sans, headings at
**800**, the token palette, the 4px space scale, the radius table and sentence case — and stays,
visibly, an analysis document. A grader must never be able to mistake a page of our claims for a
page Groupon published.

**Rejected:** dressing the explainer as a Groupon marketing/product page. It would read as
impersonation, and it would make the one place we *do* want full Groupon fidelity (R4) stop landing.

### R2 — Chapter 2's dark console survives as a labelled exception to R1.

Groupon ships **no dark theme** (`DESIGN-SYSTEM.md` §0.3), so a dark region is a deliberate
divergence. It stays because it is doing argumentative work, not decorative work: it is the device
that makes **live production observations** impossible to confuse with **supplied-CSV computations**
(004 decision E4; `FINDINGS.md` §5e opens with the conflation trap — "conflating the two voids the
package"). Chapter 2 is captured from a live API and looks like one.

The redesign may re-tune the console's palette to Groupon's neutral ramp (`#111827` surface,
`#edeff2` text). It may **not** merge the console into the page's light styling. If a different
device is proposed, it must be at least as strong, and the brief for it must say why.

**One ambiguity to settle now rather than let `006` inherit it.** `DESIGN-SYSTEM.md` §8.7 gives the
prototype's staff panel the *same* dark treatment. On this page that is harmless — R3 removes every
other dark region, so dark unambiguously means *"live catalogue, not the supplied dataset."* But
006's shell puts the staff panel and this narrative on one URL, and then dark carries two different
claims at once. **Decision: the two share the dark idiom deliberately — both mean "this is raw
observation, not our argument" — and they are disambiguated by geometry and label, not by colour.**
The console is an inline, full-width block with a catalogue banner; the staff panel is a 420px
slide-over from the right. Whoever builds 006 must keep that distinction, or pick a different device
for one of them and say so.

### R3 — the light/dark theme toggle is dropped.

Groupon is light-only. The current page carries a `theme` button plus a full `prefers-color-scheme`
block and a `[data-theme]` override — roughly a third of the CSS variable surface. Under R1 that is
now an invented feature with no source in the system. Drop it, delete the dark block, and let R2's
console be the only dark region on the page.

### R4 — add the side-by-side artifact. This is the strongest reason to use the design system at all.

`DESIGN-SYSTEM.md` §5 calls `reference/groupon-zero-results.jpg` the most important screenshot in
the folder, and §8.7 says the "what today's system would have shown" comparison "only lands if the
left-hand side is visually authentic." **The explainer currently has no such artifact.** Add one:

- **Left — what Groupon does today.** A faithful reconstruction (or the screenshot itself) of the
  real zero-results state: the `#edeff2` centred panel, "No offers available. Try removing one of
  the applied filters.", a `Clear All` link, `Results for "zzqqxwv"` with a right-aligned `0 deals`,
  and — unlabelled, unannounced — a `Similar deals` carousel of ordinary deal cards.
- **Right — what the analysis says it should do.** The abstention-first treatment: name what was not
  found, label the alternatives *as* alternatives, offer notify-me.

Two honesty rules bind this block. It must be **captioned as a real observed screenshot with its
date and query**, and the inference it invites (that this is the same shape as the F1 silent
substitution class) must be marked as inference, exactly as `DESIGN-SYSTEM.md` §5 marks it. And per
R1 the left side is a *quoted observation of Groupon's UI*, framed as evidence — not a surface we
are presenting as ours.

---

## 2. What the page is

**Audience:** a Groupon hiring panel — product and engineering leaders — clicking a link, giving it
ten minutes, and actively trying to find a claim that does not survive checking.

**The question it answers:** *when a search failed, where was the answer?*

**Argument arc — six sections in this order. The order is the finding; do not reorder.**

| # | Chapter | What it must land |
|---|---|---|
| 1 | Half of all searches end in nothing usable | The obvious metric (zero-result rate) is the wrong one. A cliff, not a gradient |
| 2 | Two results is not the same as "we found it" | **Live production Groupon**, on a dark console, behind a banner. A *different catalogue*. Shows the failure mechanism; sizes nothing |
| 3 | When a search failed, where was the answer? | Four buckets, four owners. **The spine.** Carries the band and the ordering flip |
| 4 | For one slice we can prove it was the search | The language test, then the sizing. Search is a *minority* of the recoverable opportunity |
| 5 | Replay any real query | Type a query, get its real logged counts and failure class. Unknown query → honest refusal |
| 6 | The limits, stated | What the analysis cannot establish, said before anyone has to find it |

Source of truth for every number: `outputs/story_data.json`, produced by `notebook.py`. Source of
truth for every claim: `../FINDINGS.md`. If the page and FINDINGS disagree, FINDINGS wins.

---

## 3. The design system to apply

Full document: `docs/design/DESIGN-SYSTEM.md`. Generated tokens: `docs/design/outputs/tokens.css`
(335 lines) and `tokens.json`. Curated + invented aliases: `docs/design/assets/prototype-theme.css`.
**Do not retype hex into components** — alias onto tokens, the way `prototype-theme.css` does.

### Colour roles

| Role | Token | Value |
|---|---|---|
| Brand / primary | `--color-primary` | `#017c1f` |
| Primary hover | `--background-color-primary-hover` | `#006e1b` |
| Primary subtle | `--background-color-primary-subtle` | `#e5f3e9` |
| Body text | `--text-color-body` | `#111827` |
| Muted text | `--text-color-muted` | `#70747d` |
| Tertiary text | `--text-color-tertiary` | `#9ea3ae` — **fails AA, decorative only** |
| Link | `--text-color-hyperlink` | `#0077d9` |
| Page background | `--background-color-body` | `#ffffff` |
| Muted surface | `--background-color-secondary` | `#edeff2` |
| Deeper surface | `--background-color-tertiary` | `#dee2e8` |
| Separator | `--color-separator` | `#e7e8e9` |
| Caveat / adjacency | `--color-extra` · `--background-color-extra-subtle` | `#7e40b2` on `#f5edfc` |
| Success (confirmations) | teal-800 `#006b7d` on `#e2f8fc` | **teal, not green** |
| Info | `--color-info` | `#006bc3` |
| Danger | `--color-danger` | `#cc3b3b` |
| Warning | `--color-warning` | `#e38e21` — **fails AA as text** |

**Three colour rules that are arguments, not preferences:**

1. **Green means commerce, not "good".** It carries the primary CTA, the sale price and the discount
   badge — nothing else. Never a "confident match" chip, never a confirmation toast.
2. **Purple already means "this number has a caveat"** — it is Groupon's own with-promo-code price
   colour. That is exactly what the `plausible` seam and the `can't tell` bucket are. Use purple for
   them; it extends an existing meaning rather than inventing one.
3. **Red and warning-yellow are banned for absence.** Nothing has gone wrong when the catalogue does
   not stock a thing. Red would read as an error state *and* fails contrast.

### Type

```
Nunito Sans      variable 200–1000 — everything
DM Serif Display 400 only — display/marketing. See §5: the token for it is broken.
--font-mono      ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, …  (system stack, no file)
```

| | Size | Line height | Weight |
|---|---|---|---|
| `--text-h1` | 32px | 38px | **800** |
| `--text-h2` | 24px | 29px | **800** |
| `--text-h3` | 20px | 24px | **800** |
| `--text-h4` | 18px | 22px | **800** |
| `--text-base` | 16px | 24px | 400 |
| `--text-sm` | 14px | 20px | 400 |
| `--text-xs` | **13px** (not 12) | 18px | 400 |

**Headings are 800, never 700.** That single fact does more to make a page read as Groupon than the
palette does.

### Shape, space, elevation, motion

- Space base **4px**. Content column **1200px** centred; breakpoints `lg: 991px` (not 1024),
  `xl: 1280px`.
- Radius is **not monotonic** — pick by role: badges/chips 4px (`--radius-xxs`), media 8px
  (`--radius-xs`), panels/cards 16px (`--radius-2xl`), pills `999px`. `md` (6px) is *smaller* than
  `xs` (8px).
- Elevation is composed, not shipped: standard card shadow is `0px 4px 28px -6px rgba(8,14,28,.15)`.
  Groupon's homepage barely uses it — deal cards on white have **no shadow and no border**. Reserve
  shadow for things that genuinely float.
- Motion: `--ease-out: cubic-bezier(0,0,.2,1)`, ~190ms. Short and unfussy.

### Tone

Sentence case everywhere outside the wordmark. Short, declarative, second person.

---

## 4. What is replaced

The current page's whole variable layer goes. It is a warm paper/ink editorial system with no
relationship to Groupon:

```
--paper #fbfaf7 · --paper-2 #f2efe9 · --paper-3 #e7e3da     → Groupon surfaces
--ink #1b1a17 · --ink-2 #4a4741 · --ink-3 #78736a           → Groupon text roles
--rule #ddd8cd                                              → --color-separator
--blue #2c3f8f   (structure, controls, links)               → --color-info / hyperlink
--oxide #a63a25  (absence, dead ends)                        → see §6, NOT red
--pine #2f6952   (the working state)                         → green only where it is commerce
--amber #8a6520                                              → retire; warning fails as text
--serif ui-serif Georgia …                                   → Nunito Sans
--measure 68ch  ·  .bleed 1000px                             → see §6 layout note
```

`006-one-page/SPEC.md` §3 (G5) already approved this: *"the explainer's own palette
(`--paper`/`--ink`/`--oxide`) is replaced, not layered over."* This brief executes that decision for
the standalone page, and the token layer it produces should be the one 006's Vue shell reuses —
so the re-base is done once, not twice.

---

## 5. Font delivery — measured, with the decision already made

Nunito Sans is **already vendored** in this repo via `@fontsource` at `web/app/node_modules/` and
built into `web/app/dist/assets/`. Measured woff2 subset sizes:

| subset | 400 | 700 | 800 |
|---|---|---|---|
| latin | 13.9 KB | 13.8 KB | 13.9 KB |
| latin-ext | 13.7 KB | 13.7 KB | 13.9 KB |

**Decision:** inline all six as base64 `@font-face` data URIs. ~83 KB raw → **111,365 bytes** of
`@font-face` CSS, taking the built page from 346 KB to **455 KB**. Acceptable.

**Verified, not assumed (2026-08-07).** The six subsets were base64-encoded, injected into the real
template, and pushed through both of `build_explainer.py`'s guards: **external-reference guard —
no failures; drift guard — no strays.** `src: url(data:font/woff2;base64,…)` contains no `http`,
no `<link `, no `cdn.`, and base64's alphabet cannot produce `cdn.` (no `.`). The inlining plan
builds.

*Fallback branch, if a future change breaks this:* drop the font files entirely, set
`--font-sans: system-ui, sans-serif`, and keep **headings at 800** — that weight is the load-bearing
half of the Groupon look. Record the swap; do not reach for a `<link>`.

- **latin-ext is required, not optional.** The page renders Polish (`masaż tajski`,
  `przedłużanie rzęs`) and German (`Fallschirmspringen`) query strings as evidence. Dropping it
  silently swaps those glyphs to a fallback face — inside the exact strings the language argument
  rests on.
- Weight 700 is kept: Groupon's buttons and deal-card titles are 700.
- **No mono font file.** `--font-mono` is a system stack; it costs nothing and needs no `@font-face`.
- **DM Serif Display: do not use.** Three independent reasons. `tokens.css:196` reads
  `--font-dm-serif-display: var(--font-dm-serif-display);` — **self-referential, and it does not
  deliver a usable family**; no DM Serif font file is vendored anywhere in the repo; and
  `DESIGN-SYSTEM.md` §7 says the product UI never uses it, only marketing does. If a display face is
  wanted for the masthead, that is a new decision needing its own file and its own line in the
  honesty register. *(The circular token is a real defect in the generated file — worth a line to
  whoever owns `extract_tokens.py`, stated as "does not resolve to a usable family" rather than as a
  claim about CSS resolution semantics.)*

Add `font-display: swap` and keep the `@font-face` block at the top of the inline `<style>`.

---

## 6. The grammar the page needs, and how it maps

### 6.1 The evidence/argument split must survive

The current page's central typographic rule is **prose is serif, evidence is monospace** — every
count, query string and API field is set in mono. The page's own footer *states* this rule, so
flattening the typography makes a printed sentence false.

Translation under R1: **Nunito Sans carries the argument; the mono stack carries every measured
value, query string, API field name and provenance stamp.** Keep `font-variant-numeric: tabular-nums`
on all figures. This is not decoration — it is the visual form of the grading criterion the whole
package is built on.

### 6.2 Layout

Current: a `68ch` prose column with evidence blocks breaking out to `1000px`. Groupon's content
column is `1200px`.

**Keep the narrow measure for prose** — 68ch is right for reading and 1200px is not. Set the
break-out width to Groupon's 1200px, and hang the whole thing inside a 1200px page frame. Groupon's
grid is a *product* grid; this is a document, and R1 says the document register wins where they
conflict.

### 6.3 Chart palette — a contrast problem, not a swap

Five runtime SVG figures. Current series colours are `--oxide` (dead ends), `--pine` (working),
`--blue` (structure/axes), `--amber`. Re-mapping is constrained:

| Series meaning | Use | Not |
|---|---|---|
| Dead end / failure volume | Groupon **neutral ramp** (`#585d68`, `#414652`) or `--color-info` blue | **Not red** — §3 rule 3 |
| The healthy / converting state | green — this one *is* commerce | — |
| The `plausible` seam, `can't tell`, any caveated value | **purple** `#7e40b2` / `#f5edfc` | — |
| Axes, gridlines, ticks | separator `#e7e8e9`, muted text `#70747d` | **Not** tertiary `#9ea3ae` for tick labels — 2.53:1, fails AA |
| Chapter 2's charts | stay in the console palette | — |

**Re-run `python3 docs/design/contrast_check.py` on every new pairing and paste the output into the
design's own notes.** The existing table already shows two token-legal combinations failing AA. New
combinations are not safe by assumption, and this repo is graded on checked claims.

Charts must also stay hover-legible: one shared floating tooltip node, positioned at the pointer and
clamped to the viewport.

---

## 7. Component inventory

Everything on the page, by its current class. A design agent needs this list, not "redesign the
page." Column 3 is what the component must keep doing.

| Component | Current class / id | Must keep doing | Redesign note |
|---|---|---|---|
| Masthead | `header.top`, `.eyebrow`, `.lede`, `#built` | Title, one-line lede, a mono provenance strip (searches · queries · deals · markets · date) | Groupon header geometry is a *product* header; this is a report masthead. Wordmark permitted at small size with the case-study disclosure |
| Chapter label | `.chno` | Numbered eyebrow, uppercase mono, coloured | Was `--blue`; use `--color-info` or muted |
| Provenance pill | `.src` | Says which catalogue a section's evidence is from | **Load-bearing.** Two visually distinct variants: *supplied CSV* vs *live production* |
| Two-number opener | `.versus`, `.big`, `.arrow` | 29.3% → 52.5% as the "wrong metric / right metric" hinge | Big figures in mono, tabular. Colour per §6.3, not red |
| Band bars | `.bands`, `.brow`, `.bar`, `.legend` | Three result bands with share width + s2p value | — |
| Figure frame | `figure`, `.fig-t`, `.fig-scroll`, `svg`, `.lg`, `figcaption` | Title, scrollable SVG, legend, caption | Five instances: `fig-cliff`, `fig-dist`, `fig-seam`, `fig-slope`, `fig-assum` |
| Evidence table | `.tablewrap`, `table` | Mono, scrolls inside its own container — **the body must never scroll horizontally** | — |
| Aside / caveat | `.note`, `.note .t` | An uppercase mono label plus a short qualifying statement | The page's honesty device. Must be prominent, never a footnote |
| **Live console** | `.live`, `.live-banner`, `.live h3`, `.livegrid`, `.stages`, `.q/.got/.why/.add/.sub/.nil` | Fixed dark; a banner declaring "different catalogue"; query→result exhibits; request-lifecycle stages | R2. May move to `#111827`/`#edeff2`; may not go light |
| Bucket bar + cards | `.bucketbar`, `.buckets`, `.bk` | The four location buckets, one denominator, each with its owner | **The spine.** Chapter 3's most important object |
| Class cards | `.cls`, `.ct`, `.fx` | Six failure classes with counts and fixability | Two labels are **withdrawn diagnoses** — the treatment must not restate them as facts |
| Language pair block | `.lang`, `#lang-ctrls`, `.ctrls` | English vs local dead-end rates, matched pairs, per-market table | — |
| Split / assumptions | `.split`, `.assum` | Recoverability split; per-class ranges | One range **crosses zero** deliberately — the chart must render that, not clamp it |
| **Replay simulator** | `.sim`, `.simbar`, `select#mkt`, `input#q`, `datalist#qlist`, `.chips`, `.simout` | Market select + query input + demo chips + result panel over 751 pairs | See §9. Search field: Groupon's pill + green ring + green circular submit |
| Limits | `.limits`, `.limit` | Eight plainly-stated limitations | Must read as equal in weight to the findings |
| Footer | `footer`, `#foot-src` | Source line + the typographic-rule statement | Update that sentence if §6.1's rule is reworded |
| Tooltip | `#tip` | One shared node for all five charts | — |
| Theme toggle | `#tt` | — | **Delete** (R3) |

---

## 8. The data contract — what a comp may bind

Top-level keys in `outputs/story_data.json`. Any figure in a design must map to one of these, or it
does not exist:

| Key | Contains |
|---|---|
| `headline` | searches, unique queries, deals, unique titles, markets, cities, zero rate, dead rate, dead total, 3 bands, 40 by-exact-count rows, the missing count, the tail test, the stratification test |
| `live` | pinned provenance string, the exhibit (query→result sets, the lever test, the request stages, the radius series), the appendix |
| `buckets` | total dead ends, the 4 rows, another-city concept composition, **`sensitivity`** — the three readings that produce the band and the ordering flip |
| `classes` | the 6 failure classes with pairs/searches/share |
| `void_cells` | 20 market × query always-zero cells |
| `language` | 48 matched pairs, 47 same-direction, en/local rates, gap, per-market, top pairs, all pairs, controls, caveat |
| `recovery` | healthy s2p, F4 ceiling, shares, the reconciliation, 6 assumption ranges |
| `behaviour` | per-class prototype behaviour copy, keyed by class |
| `queries` | **751** classified market+query pairs — the replay index |
| `meta` | built-from stamp, pair count, classifier accuracy, result counts seen/missing |

**Dates and provenance stamps are data slots, not copy — and this is the trap the drift guard is
most likely to spring.** "Observed on groupon.co.uk / london, 2026-08-06" typeset into a comp
becomes `2026`, `08` and `06` in the prose region, and the build fails. The current page binds every
one of them through an `id` — `#built`, `#live-pin`, `#ex-pin` — off `story_data.json.live.pinned`.
R4's caption and every `.src` provenance pill must do the same. A comp may *show* a date; the
delivered template must carry an empty `<span id="…">`.

---

## 9. Behaviour that is argument, not UI polish

Five behaviours where a normal design instinct produces the wrong page.

1. **The band renders as a band.** `nowhere` is **[43.2%, 64.7%]**, never one end. Build it as a
   *band component*; no single-value component may bind that figure. Chapter 3's three-reading chart
   — the one showing the ordering flip, where same-city overtakes nowhere — stays at full
   prominence. Not a tooltip, not an accordion, not a footnote.
2. **The unknown-query refusal is the feature.** Typing `xqzjw` in the simulator returns *"that
   query isn't in the logged set"*. This is in-character behaviour, **not an error state.** Neutral
   surface, no red, no warning icon, no "oops". A search engine that cannot say *I don't have this*
   is the failure the whole analysis is about.
3. **The diacritic normalisation announces itself.** `masaz tajski` resolves to `masaż tajski` and
   the panel *says so* before showing counts. Disclosed substitution is the fix; silent substitution
   is the defect. The design must give that disclosure line real visual weight.
4. **Live and supplied evidence can never be confused.** Every live observation carries host ·
   division · date. R2's console plus the two `.src` pill variants are the mechanism. This is the
   single highest-stakes rule on the page.
5. **Three contested figures must never render.** The adrenaline share of zeros, the supply-void
   aggregate pair count, and the pair universe (`INDEX.md` known issues #1, #6, #7). A new
   "key numbers at a glance" band is the obvious way to reintroduce one by accident — if the design
   adds a summary strip, every figure in it must be checked against that list first.

---

## 10. Acceptance criteria

Checkable statements, each true or false.

1. `python3 docs/analysis/004-data-story/build_explainer.py` exits 0 — no external reference, no
   hand-typed number, exactly one `__STORY_DATA__` token.
2. The built page opens from `file://` with the network off: fonts render, all five charts draw, the
   simulator resolves.
3. No `<link>`, no `http(s)://` outside the three exempt literals, no `cdn.`.
4. Nunito Sans loads from inlined data URIs; **latin-ext renders** — verify `masaż`, `przedłużanie
   rzęs`, `Fallschirmspringen` glyph-by-glyph, not by eye at 16px.
5. Every `h1`–`h4` is weight **800**.
6. Green appears **only** on a primary CTA. Purple appears only on caveated values. No red or
   warning yellow marks absence anywhere.
7. `contrast_check.py` re-run on the new pairings; output committed; nothing meaningful sits on
   `#9ea3ae` or `#e38e21`.
8. Chapter 2 is visually a different register from chapters 1, 3, 4, 5, 6, and its banner states the
   catalogue boundary.
9. The `nowhere` figure renders as a band in every place it appears; the ordering-flip chart is
   present and unhidden.
10. No theme toggle; no `prefers-color-scheme` block outside the console.
11. No horizontal body scroll at 1495px and at 991px; wide tables scroll inside their own container.
12. R4's side-by-side block is present, captioned with date and query, and its F1 link is marked as
    inference.
13. None of the three contested figures appears anywhere in the page source.

---

## 11. Sequencing — one line, and it matters

`006-one-page/SPEC.md` §1 is explicit: **hosted narrative + no prototype fails the brief; working
prototype + a local explainer still passes.** The current top-ranked action is `INDEX.md` 7.0
(embeddings), which unblocks 4.2 (the threshold sweep), which gates all UI work.

So: **writing this brief is cheap and executing it is not.** Execute after 4.2 reports, and write
the token layer so 006's Vue shell imports it rather than repeating the re-base. That is the
argument for doing the design work once rather than twice.

---

## 12. Files

```
docs/analysis/004-data-story/
├── REDESIGN-BRIEF.md          this file
├── explainer.template.html    the page — 362 lines of CSS to replace, one __STORY_DATA__ token
├── build_explainer.py         the three gates live here (lines 33–88)
├── notebook.py                source of truth for every number
└── outputs/
    ├── explainer.html         the built deliverable, 346 KB today
    └── story_data.json        the data contract in §8

docs/design/
├── DESIGN-SYSTEM.md           the system — §8 is the part that matters
├── outputs/tokens.css         335 generated tokens — curate, do not @import
├── assets/prototype-theme.css the curated + invented alias layer to build on
├── assets/groupon-wordmark.svg
├── reference/groupon-zero-results.jpg   ← R4's left-hand side
├── reference/groupon-homepage.jpg
└── contrast_check.py          re-run on every new pairing

docs/analysis/FINDINGS.md      every claim, tagged VERIFIED / INFERRED / CANNOT VERIFY
docs/analysis/006-one-page/SPEC.md   §3 G5 — the token decision this executes
INDEX.md                       known issues #1, #6, #7 — the figures that must not render
```
