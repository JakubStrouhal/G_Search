---
description: Diff a brief, spec or prompt (the map) against what is actually built and measured (the territory) — verify what is checkable, name the blindspots, hand the rest to /spec.
argument-hint: <@file | <nnn>-<slug> | inline question> [blindspot]  (e.g. 010-screens)
allowed-tools: Read, Grep, Glob, Bash(ls:*), Bash(git:*), Bash(python3:*), Bash(.venv/bin/python:*), Bash(npx:*), Bash(npm:*), Bash(curl:*)
disable-model-invocation: true
---

Unknowns: $ARGUMENTS

The map is not the territory. This command takes a map — a `BRIEF.md`, a `SPEC.md`, or a prompt about
to become one — and diffs it against the territory: the loaded database, the migrations, the scripts
and `FINDINGS.md`. It runs **before** the spec, not after. **It changes no file.**

## Where it sits, so nobody runs all four

| Command | The question it asks |
|---|---|
| `/reality-check` | Does the behaviour serve the searcher, or our own vocabulary? |
| **`/unknowns`** | **Does the map match the territory, and what is in the territory the map never mentions?** |
| `/review refine` | An independent adversary on a finished spec, before it is approved. |
| `/spec` | Resolves what the first three surfaced. It is the only one that writes. |

## 1. The map

- `<nnn>-<slug>` → every `.md` in that unit folder is one map; contradictions between them are findings.
- `@file` → that file.
- inline text → the prompt itself, and say so in the report; there is nothing to re-read later.
- Anything the map links — a `SPEC.md` section, a CSV in `outputs/`, an `explainer.html` — is part of it.

## 2. The territory — and always name which one

**There are two and they disagree.** Local Postgres carries the full seed; the remote
(`ewknlggenhrlftdukwme`) is behind by design — check `INDEX.md` for what is unapplied rather than
assuming either way. A grader clicks the deployed thing.

So a verdict is not "verified". It is **verified against local** or **verified against remote**.
Anything a grader will touch that has only been verified locally stays ❓ — that is not pedantry,
it is the exact shape of the last three defects in this repo.

Probes, cheapest first, **max ~10 per run**:

- `Grep` on `supabase/migrations/` — the RPC's real signature and refusal path
- `npx supabase db query` against local — what the loaded data actually contains
- re-run `validate.py`, `classify.py`, `language_test.py`, or a unit's `notebook.py`
- read `docs/analysis/outputs/*.csv` — the generated numbers, never a number retyped in prose
- `curl -sI` the deployment for anything that claims to be live
- `FINDINGS.md` for a claim already settled — if §5f and the map disagree, **§5f wins**

Anything deeper goes into the report as *needs investigation*, **with the exact command written out**
so the next session runs it instead of re-deriving it.

## 3. Claims

Read the map fully. Tag each extractable claim `C1`, `C2`, … by type:

| Type | Signal | Fate |
|---|---|---|
| FACT | "the RPC returns X", "613 queries have embeddings" | probe it (§2) |
| ASSUME | an expectation stated as background ("free text is allowed") | probe it — these are where the real breakage is |
| FUTURE | "will be", "once built", a planned step | a known unknown; it belongs in the spec's build order, first if it could invalidate the plan |
| RULE | a threshold, a default, a branch (`LOW=0.40`, chips-lead) | **provenance check.** Which script produced it? `HIGH=0.55` is a judgement and says so; a rule that cannot name its source is the same thing without the honesty |
| VAGUE | "rough", "honest", "feels like a product" | a design decision hiding in an adjective — route it, never resolve it in prose |
| HAZARD | see §4 | first, always |

**Report verdicts in this repo's three tags, not a fifth vocabulary:** **VERIFIED** (with
`file:line`, a query result, or a script run), **INFERRED** (follows from the catalogue or the design,
not observed), **CANNOT VERIFY** (the log carries no query→deal mapping, or the territory is remote and
unchecked). `FINDINGS.md` already owns that taxonomy; a parallel one is the drift `CLAUDE.md` forbids.

## 4. Hazards — reported before any analysis

There are no secrets in synthetic data. The hazard class here is **a number that will not survive
checking**, and it is graded:

1. A figure in the map that no script in the repo produces.
2. A **retired** figure — the ~18% and the 59-purchases numbers are dead; ~12% is the live one.
3. **One end of a band quoted as a point** — `nowhere` is [43.2%, 64.7%], never 43.2% alone.
4. **One accuracy number** where both error rates are owed.
5. A statement about *which* deals a query returned. `results_shown` is a count. There is no join.
   If the map asserts one, it invented it.

## 5. The blindspot pass — what the territory has that the map never mentions

The only quadrant with no home elsewhere in the pipeline, and the reason this command exists.
Walk this list; it is domain-specific on purpose:

- Does the map derive the failure class from the threshold instead of `query_classes`? (D1 forbids it,
  and the two **disagree** on real queries — `manicura`.)
- Does it treat abstain as an error state? It is 46.7% of volume and the graded requirement.
- Does it test whether stock exists at `category_l2` level? Five categories will report "exists" for
  concepts the catalogue stocks nothing for. Title level or it is wrong.
- Do `validate.py` and `classify.py`'s two hand-built `CONCEPTS` maps still agree with each other?
- Cross-language: titles are in local languages, queries are as typed. `007` showed the multilingual
  fix bridges phrasing and **not** vocabulary divergence — does the map lean on the strong version?
- Error and empty paths: what happens on failure of each step the map's happy path assumes?
- Local vs. deployed: does the thing the map promises a grader exist where the grader will click?
- Prior art: has a numbered unit already answered this? Re-deriving a finding is the cheapest waste
  in the repo.

**Max 7 cards.** Each is one line of risk plus **one sentence the owner can paste into the map**.
Fewer and sharper beats coverage.

## 6. Output — no ledger file

The pasted original wrote a `_unknowns-ledger.md` with a run-history section. **Not here.** State
lives in one place and history is `git log`; a hand-maintained log in this repo duplicated itself
inside a day. What this command finds lands in files that are overwritten in place and diff in git:

- a hazard or a contradicted claim → the owner fixes the map, or `/spec` resolves it in its decision log
- a known unknown → the spec's **Honesty register**, or the brief's *What would change the answer*
- an unknown known (a rule with no provenance) → an **open decision** for `/spec` to close with a reason
- a VAGUE claim → `/reality-check`, or build the rough thing and look at it

Re-running is idempotent because the map moved, not because a ledger tracked it.

**Report in chat, ≤ 20 lines:** hazards first · then the **top three** unknowns ordered by what they
would cost to discover late (schema > RPC contract > screen shape > copy) · each with its cheapest
route to an answer (a named probe, a decision only the owner can make, or "build it and see").
Everything else is one line under *also noted*. **No `INDEX.md` row** — this command decides nothing.

## Rules

- Every verdict carries evidence or stays ❓. Never guess the territory.
- Name which territory. "Verified" without "local" or "remote" is the defect this repo keeps hitting.
- Unknown is `unknown`. This repo is graded on whether claims survive checking.
- One follow-up per run. If the answer is "run `/spec`", say that and stop.
