---
created: 2026-08-07
updated: 2026-08-07
note: Records the embedding build — all nine acceptance criteria met, and the first real look at whether absent and stocked queries separate at all, which is what the sweep will calibrate.
---

# 007 — result

Built 2026-08-07. Spec: `SPEC.md`. Decisions E1–E8 were taken before any code.

## What exists

| Artifact | What it is |
|---|---|
| `supabase/build_embeddings.py` | Reads `services.doc` and `query_classes.q` **from the database**, encodes, emits SQL. Aborts on a wrong dimension or a failed smoke test |
| `supabase/migrations/20260807062022_query_embeddings.sql` | `query_embeddings`, keyed on `q` alone. RLS on, no policy, no grant |
| `supabase/seed_embeddings.sql` | 2.5 MB, generated. Loaded after `seed.sql` via `config.toml` `sql_paths` |

```bash
.venv/bin/pip install "sentence-transformers==5.7.0" "psycopg[binary]"
.venv/bin/python supabase/build_embeddings.py
npx supabase db reset
```

`psycopg` was not in the spec's install line and is needed — the script reads from Postgres rather
than re-deriving `doc`, which is the right trade but does cost a driver.

## Acceptance criteria — all nine met

| # | Criterion | Result |
|---|---|---|
| 1 | 75 service + 613 query vectors | **75 / 613** |
| 2 | One model, recorded | `paraphrase-multilingual-MiniLM-L12-v2`, 1 distinct value |
| 3 | Every row 384 dims | **0 rows** off-dimension |
| 4 | Smoke test | passes in all 5 markets |
| 5 | Cross-lingual, reported whatever it says | see below |
| 6 | Deterministic regeneration | same inputs → same vectors |
| 7 | Aborts on wrong width, writing nothing | **forced it**: exits, `seed_embeddings.sql` untouched |
| 8 | `anon` cannot read either table | permission denied on both, after `db reset` |
| 9 | Clean `db reset` reproduces all of it | yes |

Criterion 7 was verified by patching `DIM` to 999 and running it, not by reading the code.

## The smoke test — massage vs dining, within each market

| | DE | ES | FR | GB | PL |
|---|---|---|---|---|---|
| within massage | 0.798 | 0.765 | 0.740 | 0.754 | 0.870 |
| massage → dining | 0.338 | 0.323 | 0.294 | 0.296 | 0.322 |

A clean gap in all five. The encoder is doing something real.

## Cross-lingual — the mechanism §5b's fix depends on

Measured on `language_pairs.csv`, **the same matched set §5b computes its 42.3pp gap from**.
48 pairs had both sides in the log.

**mean 0.745 · min 0.119 · max 0.990**

| | pair | cos |
|---|---|---|
| strongest | FR `thai massage` ↔ `massage thai` | 0.990 |
| strongest | ES `city tour` ↔ `tour ciudad` | 0.986 |
| weakest | ES `sports massage` ↔ `masaje descontracturante` | **0.119** |
| weakest | PL `yoga class` ↔ `joga` | **0.153** |

Diacritics: only **one** pair exists in the log with both accented and stripped forms —
DE `rückenmassage` ↔ `ruckenmassage` = **0.959**.

**Read this honestly.** Where the local phrasing is a near-translation the model bridges almost
perfectly, and that is the F2 fix working. Where the local term is *not* a translation —
`masaje descontracturante` is "deep-tissue/knot-release massage", not "sports massage" — it does not
bridge, and no multilingual model would. **So §5b's fix is real but narrower than "language stops
mattering."** It handles phrasing, not vocabulary divergence. That belongs in Part C as a stated
limit, not smoothed over.

One diacritic pair is too few to say anything about the diacritic penalty, and this unit does not.

## First look at what the sweep will face

Max cosine per `(market, q)`, against that market's services only:

| group | n | mean | p10 | p50 | p90 |
|---|---|---|---|---|---|
| **absent** — should abstain | 437 | 0.331 | 0.181 | 0.312 | 0.503 |
| **stocked + plausible** | 314 | 0.508 | 0.276 | 0.536 | 0.690 |

**There is separation, and there is real overlap.** `absent` p90 (0.503) sits above `stocked` p10
(0.276), so no single threshold cleanly splits them — which is the expected outcome and the reason
the sweep reports two error rates rather than one accuracy number.

`001 SPEC` §1's MUST — *failure classes behave visibly differently* — looks **reachable**, but it
will cost measurable error in both directions. That number is 4.2's job to produce and publish.

## Two things that changed while building

**1. The cross-lingual check was silently passing on nothing.** The first version hardcoded three
query strings (`masaz tajski`, `masaz`, `masaz relaksacyjny`). None are in the log, so every case
printed "skipped" and the criterion was vacuous. Rewritten to read the pairs from
`language_pairs.csv` and to *discover* diacritic pairs rather than assume them. A check that cannot
find its own inputs is worse than no check, because it reports success.

**2. Query vectors are keyed on `q` alone, not `(market, q)`.** 613 rows serve 751 pairs; 58 queries
appear in more than one market. The market filter lives in the join, per D-A.

## Open

| # | Item |
|---|---|
| — | **The remote has neither the migration nor the vectors.** `db push` then load `seed_embeddings.sql` — both are writes to a hosted database and belong to the owner |
| — | The 75 descriptions are still unreviewed (4.3). If the sweep looks poor, that text is the first suspect, ahead of the model |
| — | `HF_TOKEN` is unset, so the download is rate-limited but works. Not worth fixing for a one-time fetch |
