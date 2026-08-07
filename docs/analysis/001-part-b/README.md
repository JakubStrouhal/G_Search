---
created: 2026-08-06
updated: 2026-08-06
note: Frontmatter stamped mechanically — replace with one sentence on what changed and why.
---

# 001 — Part B build spec · **forward-looking, not evidence**

**This folder contains no findings and no data.** It is the plan for the clickable prototype that
Part B requires. Nothing here proves anything about Groupon's search; do not use it to answer "how
did you come to that conclusion."

## What you are looking at

| File | What it is | Show it to Groupon? |
|---|---|---|
| `SPEC.md` | The approved build spec for the prototype: scope, required behaviour per failure class, architecture, demo script, build order | Not as a deliverable. Useful only if someone asks *how* the prototype was scoped |

## How to read it — if you read it at all

If you need to check that the prototype reflects the analysis rather than being a nice search UI
bolted on beside it, read these three sections and skip the rest:

| § | Why |
|---|---|
| **§2** | Tier assignment comes from **Part A**, not from a tuned threshold. This is the link between analysis and product |
| **§3** | Required behaviour per failure class — including **what the product does when it has no good answer**, which the brief says tells them as much as the success case |
| **§9** | Honesty register — what the prototype will admit it cannot do |

§6 (architecture) and §10 (build order) matter to whoever builds it, not to whoever grades it.

## Status and the one live caveat

Part B is **spec-approved and not built**. `INDEX.md` is authoritative.

**`SPEC.md` §3 and §4 are known to be out of date and are pending amendment** (`INDEX.md` item 7.3):

- ~~F5's row asserts a ranking cutoff~~ — **fixed 2026-08-06.** The withdrawal now rests on the
  supplied data's own terms (an absence this data cannot attribute between a cutoff and the
  generator), with the live probe as *corroboration only*. That ordering matters: the claim does not
  depend on a different catalogue.
- **F3's row still carries the UI copy *"just not in your city."*** That sentence was **false for 315
  of its 321 dead ends** — only 6 actually have the answering deal in another city. It has been fixed
  in `../004-data-story/notebook.py`, but not yet here. `INDEX.md` known issue #12.

If you quote `SPEC.md` in front of anyone, quote it knowing those two rows are stale. The corrected
versions live in `../FINDINGS.md` §5d/§5f and in the explainer.
