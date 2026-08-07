---
created: 2026-08-07
updated: 2026-08-07
note: What happened when the Claude Design comp became explainer.template.html. The comp's own
      design reasoning lives in the design project's DESIGN-NOTES.md and is not duplicated here —
      this records only the port, and the four places it deviates from the comp.
---

# Porting the redesign comp into the explainer

> **The template is hand-edited from here on.** The port ran through a one-time generator in a
> scratchpad, not a committed pipeline step, and `explainer.template.html` has been edited by hand
> since (010-screens turned the prototype door green). There is nothing to re-run, and re-running
> the generator would revert those edits. Treat the template as the source.

**Source.** Claude Design project `d0b89add-c862-4ec0-bfcc-811beb2d7233`, file `Explainer.dc.html`,
with `DESIGN-NOTES.md` beside it. The comp is a React `.dc.html` — an `<x-dc>` template using
`sc-if` / `sc-for` / `{{ }}` / `style-hover`, rendered by the project's `support.js`. The explainer
is vanilla and must open from `file://` with the network down, so none of that could ship.

**What the port did.**

1. **Resolved the comp's variant machinery at port time.** `masthead B` (report cover sheet),
   `ch2 spine B` (owner ledger), nav = launcher *and* part map, variant switcher off. The dropped
   branches are gone from the template rather than hidden — a comp variant that ships behind a flag
   is a second page nobody looks at.
2. **Rewrote the script without React.** The five figures, the tooltip and the SVG plumbing came
   across essentially unchanged, because none of it was ever framework code. The state-driven parts
   — the jump panel, the part map, the replay simulator, the chip row — were rewritten against the
   DOM. An adapter builds the shape the comp's drawing code expects out of `story_data.json`.
3. **Inlined what the comp linked.** Six base64 `@font-face` faces (latin + latin-ext × 400/700/800)
   from `@fontsource/nunito-sans` replace the Google Fonts `<link>`; the evidence screenshot becomes
   a `data:` URI. Both are `build_explainer.py` gates, not preferences. The page went 361 KB → 643 KB
   as a result, which is the cost of the offline guarantee.
4. **Bound every figure.** 102 `<span id>` slots plus the data-driven regions — the console blocks,
   the void and language tables, the six recoverability cards, the two ruled-out objections, the
   typo table, the R4 placeholder cards. The traps `DESIGN-NOTES.md` names were all real: the
   contents-list percentages, the chapter-label date pins, the console banner's hosts, the two live
   pins in the limits, the R4 caption's date, the footer stamp.

**Four deviations from the comp, all deliberate.**

- **The recoverability cards render from `recovery.assumptions`, not from the comp's card copy.**
  The comp had typed the ranges and the basis prose. Both already exist in the payload, and the
  payload's copy is the one the notebook keeps current.
- **`fillVoidTable` reads `void_cells`.** The comp hard-coded its twenty rows.
- **The prototype door's status line says what actually exists.** The comp left it as a described
  empty slot, which on a landing page reads as unfinished. The port filled it with the state at the
  time — backend local, no screen, button dashed. **010-screens has since built the screens and
  edited it again**, so the door is now green and points at `/app#prototype`. It is prose, not a
  data slot: it has already been rewritten once and will need it again.
- **The permutation test is transcribed, not computed.** The comp typed `excess +9.8pp to +14.0pp,
  z = 19.5 to 33.6` into the seam callout. Those numbers are `FINDINGS.md` §5f's, and the script
  that produced them (`scratchpad/verify_buckets.py`) is not in the repository. Rather than type
  them into the page or silently drop the claim, they sit in
  `buckets.sensitivity.permutation` with `source` and `recomputed_here: false`, and the page prints
  the attribution beside the figures.

**Chapter numbering moved, and three payload strings moved with it.** The comp reorders the page by
provenance: 1 metric · 2 buckets · 3 language + recoverability · 4 replay · 5 live production ·
6 what we built. Three cross-references inside `notebook.py`'s strings pointed at the old numbering
and were corrected — the F3 basis ("Chapter 2 tested that"), F5's `fixable` ("see chapter 3") and
`meta.note` ("the pinned live observations in chapter 5"). A rendered payload string that names the
wrong chapter is the same defect as a stale number, and harder to see.

**What has not been checked.** The page has never been opened in a browser. What ran: the drift
guard, a headless DOM smoke test (every id served, nothing undefined or NaN, no exception),
tag-balance and duplicate-id checks, and `vue-tsc` on the app build. Layout, type, the hover
tooltips and the sticky launcher are all unverified by eye. Mobile below 991px was untested in the
comp and is untested here.
