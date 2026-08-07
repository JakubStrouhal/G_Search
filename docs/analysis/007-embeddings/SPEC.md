---
created: 2026-08-07
updated: 2026-08-07
note: Approves the embedding build — locks sentence-transformers + paraphrase-multilingual-MiniLM-L12-v2 at 384 dims, a generated seed_embeddings.sql as the only load path, and a dimension assertion as build step 1 because it is the one result that can invalidate the schema.
---

# Embeddings — spec

Approved to build 2026-08-07. Brief: `BRIEF.md` in this folder.

## Thesis

**A grader who clones this repo can regenerate every vector in it with no account, no API key and
one command — and the database records which model produced them, so the threshold calibrated on
top can never be quoted against a different encoder.**

## Scope — locked

| | Component | Why |
|---|---|---|
| **MUST** | 75 service vectors → `service_embeddings` | Nothing downstream exists without them |
| **MUST** | 613 query vectors → `query_embeddings` (new table) | The sweep needs a score per `(market, q)`; 613 distinct texts cover all 751 pairs |
| **MUST** | Model id + dimension recorded in the database | A threshold is only meaningful against a named encoder. `service_embeddings.model` already exists for this |
| **MUST** | Dimension assertion that aborts | `vector(384)` is in an applied migration. A 768-dim model must fail loudly, not migrate quietly |
| **MUST** | Semantic smoke test | An encoder that returns near-identical vectors for everything would sail through every row-count check |
| **HIGH** | Generated `seed_embeddings.sql`, loaded by `db reset` | Same rule as `seed.sql`: the DB is fed by generated artifacts, never by hand |
| **NICE** | ONNX/`fastembed` runtime instead of torch | ~10× smaller install. Deferred: torch resolves today and 16 GiB is enough. Revisit only if the install fails |
| **CUT** | Embedding a query the log never saw | Needs a model call at request time — an Edge Function, a second runtime, and latency in front of a grader. `006 SPEC` §5's option A is what this builds; the fallback is named in the spec and not built |
| **CUT** | GPU / MPS acceleration | 688 texts. It is seconds on CPU. Any speedup here is time not spent on Part C |
| **CUT** | Trying two models and keeping the better | That is fitting. Part C would have to confess it. Pick one, report its error rate, say the other exists |
| **CUT** | Re-deriving `doc` | D-A already fixed it and it is in the database. This unit embeds what is stored, full stop |
| **CUT** | Any edit to the 75 descriptions | D2, and they are gated. If a description reads badly, that is 4.3's review, not this unit's licence |

## Required behaviour

Each row traces to a finding or an approved decision.

| # | Behaviour | Traces to |
|---|---|---|
| B1 | Embed exactly `services.doc` as stored — no re-derivation, no city or market token appended | D-A; `001 SPEC` §6 |
| B2 | Embed each of the 613 distinct `q` **once**, keyed on the text alone | The same string embeds identically in every market; 58 queries appear in more than one |
| B3 | Similarity is computed per market — a query is scored against that market's services only | D-A: market is a structured filter, in SQL and not in the vector |
| B4 | Record `model` and `built_at` on every embedding row | `FINDINGS.md`'s standing rule that a number carries its provenance |
| B5 | Vectors are produced offline and loaded; the browser never triggers a model call | `001 SPEC` §6; keys and model calls stay server-side |
| B6 | Regeneration is deterministic — same inputs, same vectors | The brief's acceptance bar, and "we will run it or check it" |

## What it does when it has no good answer

The graded requirement, and for this unit it has three distinct cases.

**1. A query that was never logged.** The prototype looks up `query_embeddings` by exact text after
the same diacritic folding `004`'s simulator already uses. On a miss it **says so** — *"that query
isn't in the logged set, so we can't show you what this system would do with it"* — and offers the
613 that are. It does **not** silently return the nearest logged query's results, because that would
be silent substitution, the exact failure this whole package is about. The honest refusal is the
feature; an Edge Function fallback is CUT above and stays named in Part C as the production answer.

**2. The model cannot be obtained.** No network, a moved artifact, a changed hash: **abort with the
reason**. Do not substitute a different model, and do not fall back to a smaller one. A sweep
calibrated against an unrecorded encoder is worse than no sweep.

**3. The model returns a width other than 384.** **Abort before writing anything.** The schema's
`vector(384)` is in an applied, pushed migration; a silent truncation or a quiet migration would
make every threshold downstream meaningless.

In all three the rule is the same: **stop and say why.** Nothing half-written reaches the database.

## Architecture

Only what constrains the build.

**Runtime.** `sentence-transformers` 5.7.0 on `torch` 2.13.0, in the existing `.venv` (Python
3.14.2). Both resolve today — checked, not assumed.

**Model.** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Multilingual is the whole
point: `masaż` ≡ `massage` is what `FINDINGS.md` §5b says is genuinely fixable, and the descriptions
are deliberately written in five languages so that bridge is actually tested rather than smuggled in
via English text.

**New table** — one migration, `query_embeddings`:

```sql
create table public.query_embeddings (
  q         text primary key,          -- the raw logged query, lowercased+trimmed as query_classes stores it
  embedding extensions.vector(384) not null,
  model     text not null,
  built_at  timestamptz not null default now()
);
```

Keyed on `q` alone, **not** `(market, q)` — the text is market-independent; the market filter lives
in the join. 613 rows, not 751. Same posture as `service_embeddings`: **RLS on, no policy, no
grant** — two independent locks, vectors are server-side only.

**Load path.** `supabase/build_embeddings.py` reads `services.doc` and `query_classes.q` from the
local database, encodes, and writes **`supabase/seed_embeddings.sql`**. `config.toml`'s
`sql_paths` becomes `["./seed.sql", "./seed_embeddings.sql"]` so ordering is enforced by config
rather than by memory. No hand-written SQL, same rule as `seed.sql`.

**No index.** 75 vectors. Exact scan is faster *and* has exact recall; HNSW is approximate and would
lose recall for nothing. Already documented in the table comment; restated because it is the kind of
thing a later reader "fixes".

## What the person running this has to do

Five steps. Steps 1–2 need network and are one-time.

```bash
# 1. Install the encoder into the existing venv.  ~2-3 GiB, one time, needs network.
.venv/bin/pip install "sentence-transformers==5.7.0"

# 2. Local stack must be up — the script reads docs and queries out of Postgres.
npx supabase start

# 3. Encode. First run downloads the model (~470 MB) to ~/.cache/huggingface and
#    caches it; later runs are offline. Aborts if the width is not 384.
.venv/bin/python supabase/build_embeddings.py

# 4. Load locally.
npx supabase db reset

# 5. Load on the remote. THIS IS A WRITE TO A HOSTED DATABASE — run it deliberately.
npx supabase db query --linked --file supabase/seed_embeddings.sql
```

Requirements worth stating before someone starts: **~4 GiB free disk** (16 GiB available today, so
fine, but torch is the bulk of it), **network for steps 1 and 2 only**, and **no account, no API key,
no payment at any point** — which is the property that makes the whole thing checkable.

## Acceptance criteria

Checkable statements, each either true or false.

1. `select count(*) from service_embeddings` = **75**; `from query_embeddings` = **613**.
2. Every row's `model` = `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; exactly one
   distinct value across both tables.
3. `vector_dims(embedding)` = **384** on every row.
4. **Smoke test passes:** for each market, the mean cosine similarity among that market's three
   massage documents exceeds the mean between its massage and dining documents. Reported as numbers,
   not as a pass/pass claim.
5. **Cross-lingual check, reported whatever it says:** `masaz tajski` and `masaż tajski` land within
   0.02 cosine of each other; the PL massage documents are the nearest neighbours of both. If this
   fails, it is recorded as a finding — it is the mechanism `FINDINGS.md` §5b's fix depends on.
6. Deleting `~/.cache/huggingface` and re-running reproduces byte-identical vectors.
7. `build_embeddings.py` aborts, writing nothing, when the model width is not 384 — verified by
   forcing it, not by reading the code.
8. As `anon`: `select from query_embeddings` and `from service_embeddings` both fail. Re-verified
   after `db reset`, because the local and remote default ACLs differ.
9. `npx supabase db reset` from a clean container yields all of the above with no manual step.

## Honesty register

Carries into Part C.

- **The vectors are frozen against one model, and the thresholds calibrated on them are only valid
  for it.** That is why `model` is a column. Swapping the encoder invalidates 4.2 and the sweep must
  be re-run, not adjusted.
- **This handles the 613 logged queries and nothing else.** A prototype that refuses novel input is
  a real limitation, stated rather than hidden; the production answer is a request-time embedding
  call, which is CUT here for latency and scope.
- **Embedding quality is bounded by 75 hand-written descriptions that have not yet been reviewed**
  (4.3 is open). If the sweep looks poor, the description text is the first suspect, ahead of the
  model.
- **Exact search on 75 vectors says nothing about behaviour at Groupon's real scale.** The restraint
  argument — pgvector in Postgres is correct at this size — must be stated with what it would cost at
  their volume, not silently generalised.
- **A cosine number is not relevance.** The sweep measures agreement with Part A's `coverage` labels,
  which are themselves derived from a hand-built concept map with a known cross-market gap
  (`INDEX.md` #13). The calibration inherits that.

## What would make this spec wrong

Named deliberately, because a spec that cannot fail was not specific:

- The model emits a width other than 384 → build step 1 aborts, and the schema, not the script,
  is what changes.
- `masaż` and `masaz` do **not** land near each other → the multilingual premise under §5b's fix is
  weaker than claimed, and that is a Part C correction, not a bug to tune away.
- torch fails to install on Python 3.14.2 despite resolving → fall back to the ONNX runtime listed
  as NICE, and record the swap in `model`.
- Encoding 688 texts turns out to be slow enough to matter → the approach was wrong; it should be
  seconds.

## Build order

Whatever can invalidate the plan goes first.

1. **Install, download, and assert the width is 384. Abort otherwise.** This is the only step that
   can force a schema change, and it must happen before a single vector is stored.
2. **Migration: `query_embeddings`**, RLS on, no policy, no grant. Push after local verification.
3. **Encode the 75 documents**, then run the smoke test (criterion 4) *before* touching queries — a
   broken encoder is cheapest to catch here.
4. **Encode the 613 queries**; run the cross-lingual check (criterion 5) and record the number.
5. **Emit `seed_embeddings.sql`**; add it to `config.toml` `sql_paths` after `seed.sql`.
6. **`db reset`**, then re-verify criteria 1–3 and 8 locally.
7. **Push the migration and load the remote**, then re-verify 1–3 and 8 there — because local
   verification has already been proven not to transfer.
8. Hand to 4.2. This unit produces no UI and no threshold.

## Decision log

| # | Question the brief left open | Resolution | Why |
|---|---|---|---|
| **E1** | Local model or hosted API? | **Local.** | The brief says *"we will run it or check it"*. An API pipeline cannot be re-run by a grader without their own key, which makes the central claim uncheckable |
| **E2** | Which model? | `paraphrase-multilingual-MiniLM-L12-v2`, 384 dims | Matches the applied schema, and multilingual is the mechanism §5b's fix rests on. One model, error rate published — trying two and keeping the better is fitting |
| **E3** | torch or ONNX? | **torch now**, ONNX as a named fallback | torch resolves on 3.14.2 and there is disk. ONNX is ~10× smaller but its multilingual model registry could not be confirmed without installing, and speculative installs are not spec work |
| **E4** | Where do query vectors live? | New `query_embeddings` table, keyed on `q` alone | The text is market-independent; 613 rows rather than 751. The market filter belongs in the join, per D-A |
| **E5** | How do vectors reach Postgres? | Generated `seed_embeddings.sql`, ordered after `seed.sql` in `config.toml` | Identical rule to `seed.sql`. Ordering enforced by config, not by whoever remembers |
| **E6** | What happens on an unlogged query? | **Refuse and say so**, offering the 613 that exist | Returning the nearest logged query's results is silent substitution — the failure this package exists to expose |
| **E7** | Index the vectors? | **No index** | 75 rows: exact scan is faster and has exact recall. HNSW would trade recall for nothing |
| **E8** | Embed the `gloss_en` review text too? | **No** — it never leaves the YAML | English in every document would make English queries match better because of the document rather than the model, and §5b's language test would become unmeasurable |
