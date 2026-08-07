---
created: 2026-08-07
updated: 2026-08-07
note: Opens the embedding unit — asks what has to be true before a similarity threshold can be calibrated at all, and names the model choice as the thing that would invalidate the schema.
---

# Embeddings — turn 75 documents and 613 queries into vectors that can be swept

Opened 2026-08-07. **Plan only — nothing below has been executed.**

## The question

`001-part-b/SPEC.md` §10 step 4 says to sweep HIGH/LOW against Part A's labelled pairs and report
the error rate. **That sweep cannot start.** It needs a similarity score for every one of the 751
`(market, q)` pairs, and no vectors exist: `service_embeddings` is empty and there is no query-side
store at all.

So: **what has to be true before a threshold can be calibrated, and what does the person running
this actually have to do?** Concretely — which model, which runtime, how the vectors get from a
Python process into Postgres, and what the prototype does for a query that was never embedded.

## Why now

Step 4 gates every screen (`006-one-page/SPEC.md` §1). Steps 1 and 2 are done — schema and seeds are
loaded locally and on the remote, and the 75 descriptions exist and pass the D2 guard. This is the
only thing between here and the one result that can invalidate the plan.

`INDEX.md` 4.2 is the sweep; this unit is its precondition.

## What would change the answer

Checked before writing, because the `/brief` rule says to check first:

| Fact | Status |
|---|---|
| Is a multilingual model installable on Python 3.14.2? | **Yes.** `torch` 2.13.0 and `sentence-transformers` 5.7.0 both resolve. Not a blocker |
| Is there disk for it? | **16 GiB free.** torch installs at roughly 2–3 GiB. Enough, but not comfortable — it is the reason the lighter ONNX route stays on the table |
| Does the schema already fix the dimension? | **Yes — `service_embeddings.embedding` is `vector(384)`.** A model of any other width forces a migration **and** invalidates any sweep run before the change |
| Is there a query-side store? | **No.** 613 distinct queries across 751 pairs, 58 of them appearing in more than one market. Nothing holds their vectors |
| Would an API-based model be simpler? | It would, and it is rejected: the brief says *"we will run it or check it"*, and an API-backed pipeline **cannot be re-run by a grader without their own key** |

**The one that could still point this somewhere else:** whether the chosen model actually emits 384
dimensions in the runtime we install it in. That is cheap to check and expensive to assume, so the
spec makes it build step 1 with an abort.

Nothing here makes the work unnecessary.

## Constraints

- **Must stay true:** vectors are precomputed **offline** and loaded once (`001 SPEC` §6) — no model
  latency and no keys in the browser while a grader clicks. The front end reads; the only write path
  is `demand_events`.
- **Must stay true:** `doc` is already fixed by D-A — `title · l1 · l2 · description`, no city or
  market token. This unit embeds what is in the database, it does not re-decide what goes in.
- **Must stay true:** descriptions are hand-written and gated (D2). This unit must not rewrite,
  augment, or "improve" them.
- **Reproducibility is the acceptance bar**, not embedding quality. A grader who clones the repo must
  be able to regenerate identical vectors with no account and no key.
- **Out of scope, stated not deferred:** the threshold sweep itself (that is 4.2), any UI, and
  embedding a query the log never saw — see the spec's abstention section.
- Budget: this is plumbing. If it takes more than ~2 h of wall clock beyond the model download, the
  approach is wrong.

## Done looks like

1. `service_embeddings` holds 75 rows and a query-side store holds 613, on local **and** remote.
2. The model id and dimension are recorded **in the database**, so a later sweep can prove which
   model it was calibrated against.
3. A cheap semantic smoke test passes — massage documents sit closer to each other than to dining
   documents — so a silently broken encoder cannot pass as a working one.
4. Regenerating from a clean checkout produces the same vectors, with no key and no account.
5. The sweep (4.2) can run with no further inputs.
