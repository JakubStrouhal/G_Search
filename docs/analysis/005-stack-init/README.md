# 005 — Stack init · **plumbing. Nothing to present.**

**No findings, no data, no deliverable.** This folder records one engineering decision: stand the
Supabase + Vue stack up and create **zero schema** until Part B's spec is ready to drive it.

Skip this folder entirely when explaining the analysis to Groupon.

| File | What it is |
|---|---|
| `BRIEF.md` | The question, the constraints, and the decisions recorded before any code was written |

## How to read it — the only part worth two minutes

The decisions section, because they are the kind of thing an engineering-facing interviewer may
probe:

- **Imperative migrations, not declarative** — iterate on the local DB, then generate one reviewed
  migration.
- **Local-only, not linked to a remote** — nothing before hosting needs one, and linking early costs
  budget.
- **Publishable key in the browser, never the legacy anon key and never the secret key.**
- **Empty by design.** The stack boots with zero migrations and zero tables. Schema arrives with
  Part B step 1, from `../001-part-b/SPEC.md` §10 — not before.

## Status

Steps 1–4 and 6–9 done. Local Supabase boots; `web/app` (Vue 3 + Vite + TS) builds, and its health
check reads a PostgREST 200 plus a `PGRST205` round trip, verified in-browser. Step 5 (remote link)
is **deferred until hosting**. `INDEX.md` item 4.0 is authoritative.

## Related open item

Hosting `../004-data-story/outputs/explainer.html` is tracked as `INDEX.md` items **4.4** and
**8.2** — a link beats a zip for a grader. It is currently a local file. That work belongs to this
stack, but it has not been done.
