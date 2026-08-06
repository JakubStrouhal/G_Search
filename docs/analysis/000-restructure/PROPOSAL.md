# Restructure proposal — files, commands, index, notebook

Written 2026-08-06. **Nothing has been changed yet.** This is the decision document; the folder it
sits in is itself the first example of the scheme it proposes.

---

## 1. Where the work actually stands

| | State |
|---|---|
| **Part A** | Done and defensible. Three scripts, `FINDINGS.md`, three output CSVs. Polished past the point of value. |
| **Part B** | **Zero lines built.** Two spec documents that contradict each other. |
| **Part C** | Not started. |
| **Meta** | ~2,100 lines of markdown about the work, ~950 lines of Python doing it. |

That ratio is the problem. Every simplification below is justified by one test: *does this reduce
the number of things that have to stay true?*

**The one thing that is worse than it looks:** `BUILD_SPEC.md` carries its own banner saying *"do
not build from this file"*, and `SPEC_REVIEW.md` lists six unresolved decisions (D1–D6, all
unticked) that override it — including two that change the build materially (Supabase+Vercel →
static bundle; drop the LLM-enriched descriptions as a fabrication risk). Neither has been folded
back. An agent handed "build Part B" today reads the stale draft and builds the wrong thing. This
is the top-priority fix regardless of what else you accept here.

---

## 2. What is duplicated, ranked by how much damage it does

| | What | Where | Damage |
|---|---|---|---|
| **1** | **`CLAUDE.md` known-issues list is stale.** It tells every session to fix the adrenaline `CONCEPT_TO_L2` mislabel, the two-typo-numbers ambiguity and the funnel drift. `INDEX.md` marks all three **FIXED 2026-08-05**. | `CLAUDE.md:110–116` vs `INDEX.md:136–150` | Loaded into *every* session. Actively misdirects work. |
| **2** | **Two Part B specs, the current one is the review.** | `BUILD_SPEC.md` / `SPEC_REVIEW.md` | Builds the wrong prototype. |
| **3** | **Status stated four times, four different strengths.** A = "🟡 FINDINGS is stale and is the risk" / "Analysis complete; in progress" / "Substantially done" / PLAN §6 still lists finished items as forward-looking. | INDEX, README, CLAUDE, PLAN | Known issue #5 — which itself says "3 files" and is wrong; it is 4. |
| **4** | **s2p is 11.4% and 11.5% in the same file, 11 lines apart** — and 11.5% propagated into `BUILD_SPEC.md` §4's mockup copy. The second one sits *inside* the ~303-purchase upper bound, so it is not a find-replace. **I recomputed: s2p is 11.36%, and the bound is 299, not 303.** | `FINDINGS.md:202` vs `:213` | A wrong number, and a derived number built on it, inside the handoff contract. |
| **5** | **Two hand-built `CONCEPTS` maps**, one in `validate.py`, one in `classify.py`, no shared source, free to diverge silently. `validate.py`'s map still has an unmapped bucket of 3,806 searches / 883 zeros (known issue #2, **open**); `classify.py`'s independent map is at 3.7% (`FINDINGS.md` §7, **closed**). | 2 scripts | Two maps, two states, and one issue number that reads as covering both. |
| **6** | **`INDEX.md` disagrees with itself** — Known issue #2 is open, Pending 1.2 says it was closed at 3.7%. | `INDEX.md:89` vs `:143` | The file that is supposed to win. |
| **7** | Repo layout diagram × 2; commands block × 2; core finding narrated three separate ways. | CLAUDE/README, PLAN/README/CLAUDE | Cosmetic, but each is a copy someone must maintain. |

**Not duplicated, and that is correct:** the F1–F6 taxonomy definitions exist once, in `PLAN.md`
§5. Everything else names it and links. Keep that pattern.

**A gap, not a duplicate:** the top-50 concentration stat (64.5% of searches, 71.2% of dead-ends)
lives only in `README.md:79` — the grader-facing summary — and not in `FINDINGS.md`, the handoff
contract. See §6 angle 5.

---

## 3. Proposed file structure

```
README.md          Grader entry point. Findings + how to run. Links, never restates status.
CLAUDE.md          Agent ops ONLY: what the repo is, brief constraints, commands, environment,
                   and the data model. ~45 lines. Nothing that can drift — no status table,
                   no known issues, no core-finding narrative, no defect list.
                   The data model STAYS: "results_shown is a count only, there is no
                   query->deal mapping" is what stops a fresh agent inventing a join. The
                   headline numbers move to FINDINGS.md; the structural limitation does not.
INDEX.md           State. The only place status and open defects live. See §5.

docs/brief/        Immutable supplied input. Unchanged.
docs/analysis/
  FINDINGS.md      The A→B/C handoff contract. Owns every number.
  PLAN.md          MOVED here from root. Keeps only what is unique to it:
                   §1 claims-testability, §4 live recon + retractions, §5 F1–F6 grid,
                   §7 traps. Loses §6 (INDEX owns the queue) and §3 (FINDINGS owns numbers).
  *.py, outputs/   Unchanged.
  000-restructure/ ← this proposal
  001-part-b/      SPEC.md (BUILD_SPEC + SPEC_REVIEW's D1–D6 merged, one file)
```

Root goes from 4 markdown files to 3, each with one job: **grader / agent / state**.

Three cuts you should sanity-check before I make them, because each deletes something:
- `PLAN.md` §6 phase list — INDEX's Pending queue is the live copy. Deleting removes known issue #9.
- `INDEX.md` §History (110 lines, frozen) — **safe: I verified** the two items it flags as
  "findings, not log lines" both landed in `FINDINGS.md` (§5b language test at 81.2/39.0/42.3pp,
  §5c "15 products, not 5 categories"). Nothing is lost by deleting it.
- `SPEC_REVIEW.md` — only after D1–D6 are resolved into the merged `SPEC.md`, not before.

---

## 4. The command pipeline

You named four commands for three roles. I have collapsed `/implement` and `/execute` into one —
say if that is wrong.

| Command | Reads | Writes | Role |
|---|---|---|---|
| `/brief <slug>` | `INDEX.md`, `FINDINGS.md` | `docs/analysis/<nnn>-<slug>/BRIEF.md` | The question, the constraints, what would change the answer. Creates the folder. |
| `/spec` | `BRIEF.md` in the current folder | `SPEC.md` beside it | What to build, acceptance criteria, and — the brief's hard requirement — **what it does when it has no good answer**. |
| `/implement` | `SPEC.md` | code + `RESULT.md` beside it | Spawns the build agent. `RESULT.md` records what was built, what was skipped, what is unverified. |

Folders are `<nnn>-<slug>`, numbered in creation order, one per unit of work. `/spec` refuses to
run if there is no `BRIEF.md`; `/implement` refuses if there is no `SPEC.md`. That is the "if the
folder doesn't exist" rule made mechanical rather than remembered.

`/prime` and `/wrap` stay as they are. They are the read and write sides of the index, not
pipeline stages.

**One thing to accept:** these process folders will sit next to Part A's graded artifacts in
`docs/analysis/`, as you asked. Mitigation — `README.md` points the grader at the three
deliverables only, and numbered folders sort together and read obviously as working files.

---

## 5. `INDEX.md` v2 — and a conflict worth naming

Your ask — keep the last 5–6 interactions with the decision and why — collides with a decision
this repo already made and wrote down. `.claude/index-system.md` rule 1: *"The index holds state,
not history… Nothing is append-only"*, with evidence: two sessions on the same day both logged the
same restructure and both logged adding the same `README.md`.

Both are right about different things. Git carries *what* but not *why*, and the SessionStart hook
only prints commit subjects. The version that satisfies both is **a fixed-capacity ring buffer,
not a log**: capped at 6 rows, oldest row *deleted* on write. That is bounded state — which is
what the rule actually requires — and it is not the append-only log that rotted.

```markdown
<!-- decisions:start -->
## Decisions — last 6, oldest row deleted on write
| Date | Decision | Why |
|---|---|---|
| 2026-08-06 | Collapsed /implement and /execute into one command | Four names, three roles |
<!-- decisions:end -->
```

Proposed `INDEX.md`, ~80 lines total, down from 261:

1. `<!-- state:start -->` **Now / Next** — phase, top 3 ranked actions, what is deliberately not
   being done. Injected into every session. (Keep as is; it works.)
2. `<!-- decisions:start -->` **Decisions** — the 6-row ring buffer. Also injected.
3. **Board** — A / B / C, one line each.
4. **Pending** — the queue. Keep the `| ⬜ |` glyph-in-pipes format: the hook counts open items
   with `grep -c '| ⬜ |'`, and restructuring the table silently prints `0`.
5. **Known issues** — live ones only. Struck-through fixed rows get pruned, not kept.
6. ~~History~~ — deleted (§3).
7. YAML frontmatter changelog — deleted. It is a second history for the same file.

Hook change: one `awk` block mirroring the existing `state:start` pattern. Three lines.

**Who writes the ring buffer.** If only `/wrap` does, a session that skips `/wrap` loses its
decision — the exact staleness mode the index system was designed against. Proposal: **each
pipeline command appends its own row as its last step**, and `/wrap` adds one for work that had no
command. They are already committing to a write, and the 6-row cap makes any duplication
self-healing within a few sessions.

---

## 6. The notebook — six angles, resequenced

Frame these as **Part B/C inputs, not Part A round two.** `INDEX.md`'s own state block says
"deliberately not doing: any more Part A", and that is the right instinct with B empty. Angles 1,
2 and 4 clear that bar because they feed the prototype and the writeup. Angles 3 and 6 do not.

**Setup.** `ipykernel` is installed, so an `.ipynb` runs in VS Code/Cursor today — but `scipy` and
`matplotlib` are **not**, and the system Python is PEP 668 managed. One command first:
`python3 -m venv .venv && .venv/bin/pip install scipy matplotlib pandas`.

### Angle 5 — head–tail. Already run. Here are the numbers.

I ran this before writing anything else, because it is the one that could have changed what Part B
should be:

| | Share of searches |
|---|---|
| Top 10 queries | 26.0% |
| Top 20 | 37.9% |
| **Top 50** | **64.5%** |
| Top 100 | 91.0% |

And on the addressable half — **the top 50 zero-returning queries are 80.3% of all zero-result
searches**; 284 unique queries produce all 2,633 zeros. 449 of the 613 queries appear exactly once.

**It is heavily concentrated, and the honest reading is uncomfortable: at this scale a
hand-maintained synonym list covers most of the addressable volume.**

`README.md:78–80` already has the number *and* one implication — "the fix list is short…
addressable through a ranked list of about fifty rows". What it does not have is the implication
that cuts against your own build: *"at this scale a synonym list gets you 80% of it; the embedding
path is here because it is the only thing that scales to real inventory and a real query tail."*
That is the version that survives the hiring manager running the same query themselves. Two moves:
put the stat in `FINDINGS.md` (it is a finding living only in the grader-facing summary), and put
that sentence in Part C.

### Angle 4 — strip concept mix before believing the cliff. **Do this first.** ↑ raised

You ranked this fourth. It should be second, because 52.5% is load-bearing: pending item 5.2 makes
"dead-end rate replaces zero-result rate" the headline measurement proposal in Part C. If the cliff
is partly composition, 5.2 changes. Match on concept × city, compare 1–2 vs 4+ within strata. Same
treatment for the −0.379 density correlation across 20 cells — a direction, not an effect.

### Angle 1 — demand–supply divergence. Do it, with two corrections.

- **KL will return infinity.** It is undefined wherever demand has mass and supply has none —
  which is adrenaline, i.e. precisely the concepts that matter. Use Jensen–Shannon (bounded,
  handles zeros), or just report "share of demand sitting on zero-stock concepts".
- **Supply per concept must come from applying the concept map to deal *titles*, not
  `category_l2`.** There are only 5 L2 categories, and category-level stock testing is exactly the
  bug that closed issue #1 was about. Doing it at category level here re-introduces it.
- Be honest in framing: this is a **reframe** of the known 64.2% supply void, not a new fact. It
  is still worth having — "the inventory doesn't match the demand it attracts, and search is just
  where that shows up" is the most senior sentence available in Part A — but do not sell it as a
  discovery.

### Angle 2 — allocation. Do it. Highest new content.

Given N merchant slots, which market × city × concept cells to fill. This is the only one of the
six that produces something that is not in the repo in any form, and it lands directly on Part C's
"next steps" bullet and on the Option C secondary panel that Phase 3.3 already folded in. Forces
the conversion assumption on recovered demand to be stated out loud, which is the protection
against the upper-bound trap that item 5.5 already flags.

### Angle 3 — Bayesian partial pooling. Park.

Item 1.4 already parked "Wilson CIs per failure class" as low value against an empty Part B, and
this is the same trade. If you want the shrinkage anyway, beta-binomial empirical Bayes is ~15
lines of numpy with no new dependency — but it defends a claim you are not leading with.

### Angle 6 — formalise the synthetic-data suspicion. Fold, do not add.

Pending item 1.6 already owns "write down positions on the two unresolvable items" — the missing
`results_shown = 3` and paintball's healthy conversion. A chi-square is five lines; add it inside
1.6 rather than opening a seventh workstream.

**Run order: 4 → 1 → 2.** Angle 5 is done, 3 is parked, 6 folds into 1.6.

---

## 7. What I would do, in order

1. **Fix `CLAUDE.md`.** Strip it to agent ops, ~40 lines. Stops every future session being lied to. *~15 min*
2. **Merge `SPEC_REVIEW.md`'s D1–D6 into one `SPEC.md`.** Unblocks Part B correctly. *~30 min*
3. **Recompute the upper bound, don't find-replace it.** `FINDINGS.md:213` uses 11.5% *inside* the
   ~303-purchase bound, so changing the digit leaves an arithmetically inconsistent sentence.
   Recomputed from the CSVs: on searches that returned results, CTR 38.14% / click→purchase 29.79% /
   **s2p 11.36%**, so the bound is **299**, and it stays labelled an upper bound. Propagate to
   `BUILD_SPEC.md` §4. This is pending item 5.5 — close it here. *~10 min*
4. **`INDEX.md` v2** — ring buffer, prune History and frontmatter, hook `awk` block. *~30 min*
5. **Write the three commands.** *~30 min*
6. **`/brief` → `/spec` → `/implement` on Part B.** The real work. *~3–5 h*
7. Notebook angles 4 → 1 → 2, as Part C inputs. *~1–2 h*

Steps 1–5 are ~2 hours and all of it is deletion or reconciliation. Everything after is the two
deliverables that do not exist yet.

**Open questions for you:**

- **(a)** Is collapsing `/implement` and `/execute` into one command right, or did you mean two
  stages — one that plans the build, one that runs the agent?
- **(b)** `PLAN.md` moves under `docs/analysis/` and loses §6 to INDEX's queue — agreed?
- **(c)** Who writes the decision ring buffer: every pipeline command as its last step (survives a
  skipped `/wrap`, which is the failure mode the index system was built against), or `/wrap` only
  (fewer moving parts, one writer)? I proposed the former.
