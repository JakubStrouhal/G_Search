---
created: 2026-08-08
updated: 2026-08-08
note: Part C shipped — WRITEUP.md as the canonical two pages plus the log, /app#writeup rendering it from a generated fixture, check_writeup.py verifying 64 numeric claims and mutation-tested to prove it fails. Records the one thing not verified: the two-page cap is measured at 1.79 A4 pages, never printed.
---

# 011-writeup — result

Built 2026-08-08. Part C existed nowhere; it now exists twice over, from one source.

## What shipped

- **`WRITEUP.md`** — 1,393 words before the log, covering the brief's four bullets in the brief's
  own order, then the log (hours, tools, what the tools got wrong).
- **`/app#writeup`** — a lazy hash route on `App.vue`, same shape as `#prototype` and `#stack`.
  Renders the generated fixture: document on a white sheet, evidence rail visibly outside it,
  the log as a second sheet.
- **`check_writeup.py`** — 64 numeric claims, every one resolving to a figure recomputed from the
  CSVs / `query_classes.csv` / the sweep summary, or to a 20-entry allowlist that names the file
  owning each number.
- **`build_writeup.py`** — markdown → block JSON. Small parser, no runtime Markdown dependency, and
  spans rather than HTML strings so nothing needs `v-html`.
- **The door flipped in the same change**, per `010-screens` decision 14: `SiteIndex.vue`'s Part C
  card went from `status: 'not started'` / `pending: 'Not yet written.'` to a live link.

## The defect this closed

The explainer's deliverables bar labelled `/app` **"Part C — The writeup, with the package →"**.
`/app` rendered a card that said *Not yet written.* A grader following the package's own
navigation arrived at an admission. That is now a link to a document.

## Verified

| # | Check | Result |
|---|---|---|
| 1 | `npm --prefix web/app run build` (`vue-tsc -b` first) | exit 0 |
| 2 | `check_writeup.py` | PASS, 64 claims, 93 figures recomputed |
| 3 | **Mutation test** — `52.5%` → `53.5%` in the writeup | exit **1**, names the number; reverted, exit 0 |
| 4 | `grep -rE '43\.2\|64\.7\|46\.7\|32\.4\|20\.9\|11\.5' web/app/src/` | no match — `010` criterion 12 intact |
| 5 | Rendered at `/app.html#writeup`, 1280 wide | document, table, list, rail and log all render; console clean |
| 6 | **Built with `.env.local` removed**, served from `dist`, `/app#writeup` | renders in full, no error card, console clean. `grep supabase` on the `WriteupPage` chunk: **0** |
| 7 | All three `/app` cards | `Part A → /`, `Part B → #prototype`, `Part C → #writeup`, all `chip--live` |
| 8 | Print layout measured against A4's content box (180 × 269 mm) | **1.79 pages**, 217 px of headroom |

## What is NOT verified, and it is the claim that matters most

**"Two pages" was measured, not printed.** Check 8 clones the document into a box the width of A4's
content area, applies the same type sizes the `@media print` block sets, and measures the flow —
which is a real measurement of *height*, not of pagination. Widows, orphans and `break-after: avoid`
are the printer's decisions, not that box's. The 217 px of headroom exists so that those decisions
cannot spill onto a third sheet, and 10pt was rejected for exactly this reason (it measured 1.95
pages — inside the cap, with 47 px to spare, which is not a margin). **The owner's Cmd-P is the
test that counts.**

## Decisions

| # | Question | Resolution | Why |
|---|---|---|---|
| 1 | Where does Part C live — a page, a PDF, or markdown? | **All three are one artifact**: markdown is canonical, the page renders it, print gives the PDF | A hosted link is what the brief asks for; a document with a page cap is what it asks *for*. Splitting them creates the second copy that drifts |
| 2 | Does the surface expand beyond two pages? | **No — strict document column, evidence rail visibly outside it** | This repo's house style runs long and the cap is the only hard constraint the brief places on Part C. A rail that reads as part of the writeup would break it silently |
| 3 | Does the log count against the two pages? | **No.** The brief says "Two pages maximum" and then "And a short log" — two requests | Separate section, own printed sheet, word count taken before it |
| 4 | Prose in the component, or a fixture? | **Fixture, generated from the markdown** | `010` criterion 12 forbids the headline figures under `web/app/src/`, and Part C is made of them. Keeping the prose in `docs/` keeps the criterion true by construction, not by memory |
| 5 | Which supply-void definition does Part C lead with? | **`classify.py`'s 178 / 1,689**, with `validate.py`'s 185 / 1,691 named as the alternative | Known issue #6 says decide and say why. The prototype acts on the first; a writeup quoting a number its own deliverable does not implement is the drift this package refuses |
| 6 | Hours | **8:01 owner wall-clock, supplied by the owner.** Agent execution recorded separately per unit and *not* added | `004/RESULT.md` set the policy: an agent-side estimate is a fabrication in a log whose purpose is honesty about effort. Git gives a 3-day span, which is a ceiling, not a measurement |
| 7 | How many tools-log entries? | **Three**, from `FINDINGS.md` §9's twelve | The brief asks for "one or two sentences on anything the tools got wrong". A twelve-row table answers a question nobody asked |
| 8 | Print type size | **9.5pt / 1.36, chosen by measuring three candidates** | 9.25pt measured 1.68 pages (wasteful), 10pt measured 1.95 (no margin), 9.5pt measures 1.79 |

## Left

- **Nothing is pushed.** Every check above ran on the dev server or a local `dist` build. Vercel
  builds what is in the repository, so the deployed `/app` still shows *"Not yet written."* until
  commit → push → deploy. Re-probe `/app#writeup` on the deployment afterwards.
- The owner's print check (see above).
- `INDEX.md` rows 5.1–5.4 and 3.4 are answered *inside* the writeup; they are closed there rather
  than each producing its own artifact.
