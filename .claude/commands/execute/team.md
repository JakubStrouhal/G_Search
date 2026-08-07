---
description: Orchestrate the build as an agent team — decompose an approved SPEC into tasks, spawn be/fe/reviewer teammates, drive it end to end. Refuses to run without a spec.
argument-hint: [<nnn>-<slug>]  (optional — defaults to the highest-numbered folder with a SPEC.md)
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, Agent, TaskCreate, TaskUpdate, TaskGet, TaskList, SendMessage
disable-model-invocation: true
---

Orchestrate: $ARGUMENTS

**You are the lead. You do not write code.** The main session is the team lead for its lifetime —
that is fixed, teammates cannot spawn teammates, and there is no orchestrator agent file because
there is nothing to spawn it as. Your job is decomposition, assignment, verification and status.

`/execute:implement` is the single-agent path and is the right one for a unit that fits one lane.
Use this command only when the work genuinely splits across `supabase/**` and `web/app/**`.

## 0. Preconditions — check, do not assume

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` must be set. It is, in `~/.claude/settings.json`. If a
  teammate spawn silently produces a subagent instead, that is the symptom of it being unset.
- `.claude/agents/` must contain `be-builder`, `fe-builder`, `reviewer`.
- Teammates load `CLAUDE.md` and project skills but **inherit none of this conversation.** Every
  spawn prompt carries the spec path, the task, and the acceptance criteria in full.
- Teammate permission prompts surface in **your** session. Answer them; do not leave a teammate
  blocked on one.

## 1. Find the spec

Default: the highest-numbered `docs/analysis/<nnn>-<slug>/` containing a `SPEC.md`.

**No `SPEC.md` → stop.** Say "run `/spec` first" and do nothing else. Do not infer a spec from the
brief, from `INDEX.md`, or from this conversation.

**A spec marked awaiting approval is not an approved spec.** Check its `INDEX.md` Pending row. Tasks
derived from an unapproved spec may be created, but they are created **blocked**, and no teammate is
assigned to them until the owner approves. Say which tasks those are in your report.

## 2. Read the spec in full, then run its gate yourself

Read `SPEC.md` completely, and `docs/analysis/FINDINGS.md` for the findings behind it. Then find the
spec's build-order step 1 — the spec is required to put whatever could invalidate the plan first.

**Run that step yourself, before spawning anyone.** If it fails, the spec is wrong and the build
does not start. Report that; it is a successful outcome for this command.

## 3. Decompose — and do not manufacture parallelism

One task per build-order step, split further only where a step spans two lanes. For each:
`TaskCreate` with the subject, the spec section it comes from, its acceptance criteria, and its
lane. Then `TaskUpdate` to set `blockedBy` from the spec's own gates.

**Respect the gate, and say it out loud in your report.** In `001-part-b/SPEC.md` §10 the first four
steps — migrations/seeds → the 75 descriptions → offline embeddings → the threshold sweep — are
strictly sequential, single-lane, and **step 4 gates every UI task below it.** That is the majority
of the remaining critical path and it does not parallelise. A four-column phase table that pretends
otherwise is a plan that will deadlock on its own dependencies.

- **Single lane to the gate.** `be-builder` alone. Do not spawn `fe-builder` yet; there is nothing
  for it to build against and its screens depend on bands that do not exist.
- **Fan out after the gate.** Screens by behaviour, demand loop, staff panel, acquisition brief and
  coverage table split cleanly between the lanes.
- Aim for **5–6 tasks per teammate.** Too small and coordination costs more than it saves; too large
  and a teammate works for an hour in a direction nobody checked.

Tasks the owner must do personally — anything the spec reserves, such as `001 SPEC` D2's
hand-written descriptions — are created, assigned to nobody, and named as owner tasks in your
report. Do not hand them to a builder to unblock yourself.

## 4. Spawn, with lanes that cannot collide

Two teammates editing one file is an overwrite. The lanes are disjoint by construction — enforce it:

| Teammate | Agent type | Owns |
|---|---|---|
| `be` | `be-builder` | `supabase/**`, pipeline scripts under the unit folder, regenerated `outputs/` |
| `fe` | `fe-builder` | `web/app/**` |
| `check` | `reviewer` | nothing — read-only |

**You alone write `INDEX.md`.** Status lives in one place; four writers is the drift that rule
exists to prevent. Nobody writes `docs/analysis/FINDINGS.md` or `docs/brief/**`.

Name them in the spawn instruction so you can address them later. Give each the spec **path**, not a
summary — a summarised spec is a spec that lost its CUT list.

For any task that could invalidate the plan rather than merely execute it, **require plan approval**
and say what you will approve on: a plan that reports the sweep's error rate both directions gets
approved; a plan that tunes thresholds until they look right does not.

## 5. Drive it

- Let teammates finish. If you catch yourself implementing, stop — assign it.
- On each idle notification, read the report and check the claim before you believe it. Run the
  build, run `db reset`, look at the output. **An agent reporting success is not evidence.**
- Send `check` in at each phase boundary and before you flip any `INDEX.md` row.
- Task status lags: teammates sometimes fail to mark a task complete, which blocks its dependents.
  If a task looks stuck, verify whether the work is actually done and update it yourself.
- A teammate that stops on an error stays stopped. Message it directly or spawn a replacement.

## 6. Independent validation — not the reviewer teammate

The `reviewer` teammate is an in-team conformance check. It is **not** the gate `CLAUDE.md`
requires. Before presenting the build as working, run the same Codex pass `/execute:implement` uses:

```bash
bash .claude/hooks/codex-interview.sh implement docs/analysis/<nnn>-<slug>/SPEC.md
```

Exit 0 → verify each material finding against the repo yourself. Exit 2 → fix the path and re-run.
Exit 3 → report **"spec conformance unvalidated — reviewer unavailable"**. **An unavailable reviewer
is unknown, never a pass.**

## 7. Close out

Write `RESULT.md` beside the spec in the shape `/execute:implement` §5 specifies — what was built,
what was skipped and why, what is unverified, where the spec was wrong, and the hours. **Log the
real hours**, including the team's; the brief requires it and an honest 18-hour log beats a
fictional 5-hour one.

Then update `INDEX.md`: flip closed Pending rows to ✅ with what was *established* — a number, a
path, a verdict — not "done". Add any defect the build created to Known issues. Add a decision row
per `.claude/decision-row.md` only if building decided something the spec did not.

Shut teammates down by name when their lane is finished.

## 8. Report, ≤8 lines

Tasks created · who owns what · **where the gate is and what it blocks** · what runs · what does not
· what is unverified · Codex's verdict or that it was unavailable · the next action.

> Half-done is reported as half-done. A build reported as working that has not been run is the one
> failure this repo cannot afford.
