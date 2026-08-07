"""Generate supabase/seed.sql — the mechanical seeds for Part B.

    python3 supabase/build_seed.py && npx supabase db reset

`config.toml` has `[db.seed] enabled = true, sql_paths = ["./seed.sql"]`, so
`db reset` applies migrations and then this file, in one command.

WHY THIS IS A SCRIPT AND NOT A HAND-WRITTEN .sql. CLAUDE.md: regenerate
`docs/analysis/outputs/` from the scripts and seed the DB from those outputs —
never hand-type a number into a migration. The repo's recurring defect is a stale
figure living inside a derived one (the 11.5 -> 11.4 -> 299 episode). A generated
seed cannot drift from the analysis; a typed one silently can.

WHAT THIS DOES *NOT* SEED, deliberately:
  services.description   Hand-written, 75 lines, D2. LLM enrichment could write
                         "adrenaline, thrills" onto the activities deals, collapse
                         F4 into F1, and make the central finding an artifact of
                         generated text. A separate committed file fills these.
  services.doc           Built from title + categories + description, so it waits
                         on the descriptions.
  service_embeddings     Precomputed offline (SPEC §6). Loaded by its own step.

Sources, all of them already in the repo:
  docs/brief/deals.csv                            -> cities, deals, services
  docs/analysis/classify.py STOCK_TITLE           -> service_concepts  (imported, never retyped)
  docs/analysis/outputs/query_classes.csv         -> query_classes
  docs/analysis/outputs/inventory_location.csv    -> demand_events
"""
import contextlib
import importlib.util
import io
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "brief"
OUTPUTS = ROOT / "docs" / "analysis" / "outputs"
SEED = ROOT / "supabase" / "seed.sql"

# The log is a single month; demand_events seed rows are a 30-day aggregate, not
# daily events, and occurred_on records the period end. Read, never assumed.
LOG_END = pd.read_csv(BRIEF / "search_log.csv")["date"].max()

# classify.py prints its full report on import. Swallow it — we want the map, and
# importing it is the point: the repo already carries two hand-built concept maps
# that can drift (CLAUDE.md), and a third copy in this file would be a third thing
# to keep in sync.
_spec = importlib.util.spec_from_file_location("cl", ROOT / "docs" / "analysis" / "classify.py")
_cl = importlib.util.module_from_spec(_spec)
with contextlib.redirect_stdout(io.StringIO()):
    _spec.loader.exec_module(_cl)
STOCK_TITLE = _cl.STOCK_TITLE

deals = pd.read_csv(BRIEF / "deals.csv")
qc = pd.read_csv(OUTPUTS / "query_classes.csv")
loc = pd.read_csv(OUTPUTS / "inventory_location.csv")


def lit(v):
    """One SQL literal. Escaping lives here so no caller has to think about it."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
        return "null"
    if isinstance(v, (bool,)):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def insert(table, cols, rows, chunk=200):
    """Multi-row INSERTs in batches — one statement per chunk keeps the file readable."""
    out = []
    rows = list(rows)
    for i in range(0, len(rows), chunk):
        values = ",\n  ".join("(" + ", ".join(lit(v) for v in r) + ")" for r in rows[i:i + chunk])
        out.append(f"insert into public.{table} ({', '.join(cols)}) values\n  {values};")
    return "\n".join(out), len(rows)


parts, counts = [], {}


def emit(table, cols, rows):
    sql, n = insert(table, cols, rows)
    parts.append(f"\n-- {table}: {n} rows\n{sql}")
    counts[table] = n


# -- cities ------------------------------------------------------------------
emit("cities", ["market", "city"],
     deals[["market", "city"]].drop_duplicates().sort_values(["market", "city"]).itertuples(index=False))

# -- deals: verbatim ---------------------------------------------------------
dcols = ["deal_id", "market", "city", "title", "category_l1", "category_l2",
         "price_usd", "rating", "num_ratings", "is_bookable"]
emit("deals", dcols, deals[dcols].itertuples(index=False))

# -- services: the 75 distinct (market, title). description/doc stay null. ----
# Verified against deals.csv: no title crosses a market and title -> category is
# 1:1, so this drop_duplicates cannot silently merge two different meanings.
svc = (deals[["market", "title", "category_l1", "category_l2"]]
       .drop_duplicates().sort_values(["market", "title"]))
assert svc.groupby(["market", "title"]).ngroups == len(svc), "title -> category is not 1:1"
emit("services", ["market", "title", "category_l1", "category_l2"], svc.itertuples(index=False))

# -- service_concepts: THE JOIN PATH the cross-city gate needs ----------------
# Derived by RUNNING STOCK_TITLE's regexes, not by retyping them.
titles_lower = svc["title"].str.lower()
concept_of = {}
for concept, pattern in STOCK_TITLE.items():
    for _, r in svc[titles_lower.str.contains(pattern, regex=True, na=False)].iterrows():
        concept_of[(r["market"], r["title"])] = concept

sc_rows = [(m, t, concept_of.get((m, t)), concept_of.get((m, t)) is None)
           for m, t in zip(svc["market"], svc["title"])]
emit("service_concepts", ["market", "title", "concept", "is_generic_proxy"], sc_rows)
counts["service_concepts (no concept)"] = sum(1 for r in sc_rows if r[2] is None)

# -- query_classes: the Part A contract, verbatim -----------------------------
qcols = ["market", "q", "concept", "coverage", "failure_class", "searches", "zeros",
         "deads", "clicks", "buys", "zero_rate", "dead_rate", "city_spread",
         "deals_stocking", "is_english", "thin_n", "dead_nowhere", "dead_same_city",
         "dead_another_city", "dead_cant_tell"]
emit("query_classes", qcols, qc[qcols].itertuples(index=False))

# -- demand_events: the seeded baseline --------------------------------------
# SPEC §5: seed from the log so a fresh instance shows real volume (GB London
# adrenaline = 222) rather than "1 search". 'unmapped' becomes null, because
# "we do not know what was asked" is not a concept.
dem = loc[["market", "city", "concept", "q", "searches"]].copy()
dem["concept"] = dem["concept"].where(dem["concept"] != "unmapped", None)
emit("demand_events", ["market", "city", "concept", "raw_query", "occurred_on", "source", "n"],
     ((r.market, r.city, r.concept, r.q, LOG_END, "seed", int(r.searches))
      for r in dem.itertuples(index=False)))

header = f"""-- GENERATED BY supabase/build_seed.py -- DO NOT EDIT BY HAND.
-- Regenerate:  python3 supabase/build_seed.py && npx supabase db reset
--
-- Sources: docs/brief/deals.csv; docs/analysis/classify.py STOCK_TITLE (imported,
-- not retyped); docs/analysis/outputs/{{query_classes,inventory_location}}.csv.
--
-- NOT seeded here, on purpose: services.description (hand-written, 75, D2),
-- services.doc (needs the descriptions), service_embeddings (precomputed offline).
--
-- demand_events seed rows are a 30-DAY AGGREGATE over {LOG_END[:7]}, not daily events:
-- n is the month's search count and occurred_on is the period end ({LOG_END}).

truncate public.demand_events, public.service_embeddings, public.service_concepts,
         public.services, public.deals, public.cities restart identity cascade;
"""

SEED.write_text(header + "\n".join(parts) + "\n")

print(f"wrote {SEED.relative_to(ROOT)}  ({SEED.stat().st_size / 1024:.0f} KB)")
for k, v in counts.items():
    print(f"  {k:34} {v:5d}")
print(f"\n  demand_events n sums to {int(dem.searches.sum()):,} — the whole log, losslessly")
