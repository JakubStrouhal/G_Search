---
created: 2026-08-08
updated: 2026-08-08
note: How to read and regenerate the 011-writeup unit — which file is canonical, why the prose lives in docs/ rather than in a component, and which quoting rules bound the writing.
---

# 011-writeup — Part C

**Presentable.** `WRITEUP.md` is the deliverable; everything else here exists to keep it true.

| File | What it is |
|---|---|
| `WRITEUP.md` | **Part C itself** — the brief's two pages, then the log. Canonical; edit this and nothing else. |
| `check_writeup.py` | Every number in the writeup must resolve to a recomputed figure or a named source. Exits 1 otherwise. Mutation-tested. |
| `build_writeup.py` | `WRITEUP.md` → `outputs/writeup.json`, the block fixture the page renders. |
| `outputs/writeup.json` | Generated. Never hand-edited. |
| `RESULT.md` | What was built, what was cut, what is unverified. |

```bash
python3 docs/analysis/011-writeup/check_writeup.py   # must pass before quoting anything
python3 docs/analysis/011-writeup/build_writeup.py   # regenerate the fixture after any edit
```

## How to read it

The writeup renders at **`/app#writeup`** and lives here as markdown. The two are the same bytes —
the page imports the generated fixture through the `@writeup` alias rather than carrying a second
copy of the prose. That is not tidiness: `010-screens/SPEC.md` acceptance criterion 12 greps
`web/app/src/` for the headline figures and must find none, and Part C is prose full of exactly
those figures. Keeping the text in `docs/` satisfies the criterion by construction.

**The log is not part of the two pages.** The brief asks for the writeup ("two pages maximum") and
then, separately, for a short log. So `## The log` is the split point in the markdown, the word
count is taken before it, and it starts its own sheet in print.

## What binds the prose

`FINDINGS.md` §8 owns the quoting rules and `INDEX.md`'s known issues own the rest. The ones this
document had to obey: lead with 52.5% and never widen it to 57.7%; never quote one end of the
`nowhere` band; quote ~12% and never ~18%; no adrenaline share anywhere while the two concept maps
disagree; never imply real Groupon lacks paintball; and pick one supply-void definition and say why.
