"""Generate outputs/chips.json — the curated chip row for the prototype.

    python3 docs/analysis/010-screens/build_chips.py

WHAT IS CURATED AND WHAT IS DERIVED, because the difference is the whole point.

CURATED (hand-listed below, and it has to be): the *query strings and cities* of
the demo chips. 010 SPEC's honesty register says so plainly — "the chips are
curated", chosen so every render state is reachable in one click. Free text stays
open precisely so the demo is not only its happy paths.

DERIVED (never typed): every *band*, flag and count. Each chip is probed through
`public.search_deals` on the live local database and the answer is written down.
A chip therefore cannot claim a state the RPC does not actually return, and if a
threshold moves this file changes — which is the point: `fe` asserts against it,
so a band that shifts surfaces as a failing fixture instead of as a screen that
quietly renders the wrong state.

ALSO DERIVED: the 15 band chips (5 markets x 3 bands). For each market the
default city is the one with the most seeded June searches, and the chip is the
highest-volume logged query that actually renders that band there. No market's
representative is a personal pick.

THE SCRIPT WRITES NOTHING. `search_deals` inserts a `source='live'` demand row on
every abstention, and roughly half of these probes abstain. Building a fixture
must not move the demand table, so the whole probe runs inside a transaction that
is ROLLED BACK. Verified: demand_events is byte-identical before and after.

Re-run after `npx supabase db reset`. Embeddings are deterministic, so a clean
re-run reproduces this file exactly; if it does not, a threshold or a seed moved
and that is a finding, not a merge conflict.
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "outputs" / "chips.json"
PGURL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

# The three bands `search_deals` can return for a logged query, in the order the
# chip row should read: works, hedged, honest-nothing.
BANDS = ["confident", "adjacent", "abstain"]

# -- THE CURATED SET ----------------------------------------------------------
# (market, city, query, role). The role is a CLAIM ABOUT WHY THIS CHIP EXISTS and
# it is ASSERTED against the probe below — if `escape room` in Birmingham stops
# being near-empty, this script aborts rather than shipping a chip that lies.
#
# Sources: 010 SPEC acceptance criteria 1, 3, 6, 7 and the lead's additions of
# 2026-08-07 (both floor branches explicit, one cross-market chip).
PINNED = [
    # Criterion 1 names six of the fifteen band chips outright. Honour the names —
    # deviating from a spec example silently is how a fixture stops being the
    # spec's. The BAND is still probed, never assumed; the nine unnamed cells are
    # filled by the volume rule below.
    ("GB", "London",     "gym",                "spec_named"),
    ("GB", "London",     "indian restaurant",  "spec_named"),
    ("GB", "London",     "paintball",          "spec_named"),
    ("DE", "Berlin",     "personal trainer",   "spec_named"),
    ("DE", "Berlin",     "kart fahren",        "spec_named"),
    ("DE", "Berlin",     "wildwasser rafting", "spec_named"),

    # Criterion 1 — the five near-empty chips.
    ("DE", "Köln",       "kart fahren",     "near_empty"),
    ("ES", "Barcelona",  "paseo en globo",  "near_empty"),
    ("FR", "Paris",      "karting",         "near_empty"),
    ("GB", "Birmingham", "escape room",     "near_empty"),
    ("PL", "Kraków",     "masaż dla par",   "near_empty"),

    # Criterion 6 — both directions of band-vs-Part-A disagreement, shown not tuned.
    ("ES", "Madrid",     "manicura",        "disagreement"),   # abstain vs Part A `stocked`
    ("ES", "Madrid",     "paseo en globo",  "disagreement"),   # adjacent vs Part A `absent`

    # Criterion 3 — both branches of the 0.30 alternatives floor. Without the
    # second one the floor looks like a way of never showing alternatives at all.
    ("GB", "London",     "paintball",           "floor_suppress"),
    ("GB", "London",     "eyelash extensions",  "floor_show"),

    # Lead, 2026-08-07 — the cross-market case. query_embeddings is keyed on `q`
    # (613) and query_classes on (market, q) (751), so a query logged in one
    # market resolves in all five and Part A has no verdict on it here. 2,314 of
    # 3,065 combos are in this state and a curated-chips-only click never sees it.
    ("DE", "Berlin",     "helicopter tour", "cross_market"),

    # Criterion 2 — the normalisation disclosure.
    ("PL", "Warszawa",   "masaz tajski",    "normalised"),
]

# What each role asserts about the probe. Abort, never warn: a fixture that
# ships a false claim is worse than no fixture.
ROLE_ASSERTS = {
    # A spec-named band chip asserts only that it is one of the three logged
    # bands — which band is the RPC's to say, not this file's.
    "spec_named":     lambda r: r["band"] in BANDS,
    "near_empty":     lambda r: r["near_empty"] is True,
    "city_empty":     lambda r: r["city_empty"] is True,
    "disagreement":   lambda r: r["staff"]["band_agrees_with_part_a"] is False,
    "floor_suppress": lambda r: r["band"] == "abstain" and r["alternatives_above_floor"] is False,
    "floor_show":     lambda r: r["band"] == "abstain" and r["alternatives_above_floor"] is True,
    "cross_market":   lambda r: r["staff"]["part_a_logged_here"] is False,
    "normalised":     lambda r: r["normalised"] is True,
}


def psql(sql: str) -> str:
    """One rolled-back transaction, one JSON blob out. -A -t so nothing decorates it."""
    p = subprocess.run(
        ["psql", PGURL, "-A", "-t", "-v", "ON_ERROR_STOP=1", "-f", "-"],
        input=sql, capture_output=True, text=True,
    )
    if p.returncode != 0:
        sys.exit("ABORT — psql failed. Is the local stack up (`npx supabase start`)?\n" + p.stderr)
    return p.stdout


values = ",\n    ".join(
    "(" + ", ".join("'" + v.replace("'", "''") + "'" for v in row[:3]) + ")" for row in PINNED
)

# One statement set, wrapped in begin/rollback. Every candidate is probed through
# the real RPC — not a re-implementation of its banding, which is exactly how a
# fixture drifts away from the thing it is meant to pin down.
SQL = f"""
begin;

create temporary table _probe on commit drop as
with defaults as (
  select market, city from (
    select market, city,
           row_number() over (partition by market order by sum(n) desc, city) as rn
    from public.demand_events where source = 'seed' group by market, city
  ) t where rn = 1
),
pinned (market, city, q) as (values
    {values}
),
candidates as (
  -- POOL 'qc' — every logged query in its market's busiest city: where the 15
  -- band chips come from, by volume, with no hand-picking
  select d.market, d.city, qc.q, qc.searches, 'qc' as pool
    from public.query_classes qc join defaults d on d.market = qc.market
  union all
  -- POOL 'seed_cell' — every (market, city, query) the June log actually
  -- contains. This is where the city_empty chip comes from, and it has to be a
  -- different pool: city_empty is a property of a CITY, so the busiest-city
  -- restriction above would hide it. Ranking by real searches in that real city
  -- keeps the chip a thing people did, not a combination that merely triggers.
  select de.market, de.city, de.raw_query, 0, 'seed_cell'
    from public.demand_events de where de.source = 'seed'
  union all
  select p.market, p.city, p.q, coalesce(qc.searches, 0), 'pinned'
    from pinned p left join public.query_classes qc
      on qc.market = p.market and qc.q = p.q
),
folded as (
  select market, city, q,
         max(searches) as searches,
         bool_or(pool = 'pinned')    as is_pinned,
         bool_or(pool = 'qc')        as in_qc_pool,
         bool_or(pool = 'seed_cell') as in_seed_pool
    from candidates group by market, city, q
)
select f.market, f.city, f.q, f.searches, f.is_pinned, f.in_qc_pool, f.in_seed_pool,
       coalesce((select sum(de.n) from public.demand_events de
                  where de.source = 'seed' and de.market = f.market
                    and de.city = f.city and de.raw_query = f.q), 0) as seed_searches,
       public.search_deals(f.market, f.city, f.q) as r
  from folded f;

select json_build_object(
  'probes', (select json_agg(json_build_object(
                'market', market, 'city', city, 'query', q,
                'searches', searches, 'is_pinned', is_pinned,
                'in_qc_pool', in_qc_pool, 'in_seed_pool', in_seed_pool,
                'seed_searches', seed_searches,
                'r', r)) from _probe),
  'defaults', (select json_agg(json_build_object('market', market, 'city', city))
                 from (select distinct market, city from _probe where in_qc_pool) d),
  'config', (select row_to_json(c) from (
                select low, high, alt_floor, model, calibrated_on from public.search_config) c)
);

rollback;
"""

# The fingerprint above is fiddly inside one statement; take it separately and
# cleanly, before and after, as the actual proof that nothing was written.
FINGERPRINT = ("select json_agg(t) from (select source, count(*) as rows, sum(n) as n_sum "
               "from public.demand_events group by source order by source) t;")

before = psql(FINGERPRINT).strip()
raw = [ln for ln in psql(SQL).splitlines() if ln.strip().startswith("{")]
after = psql(FINGERPRINT).strip()

if before != after:
    sys.exit(f"ABORT — the probe moved demand_events, so the rollback did not hold.\n"
             f"  before: {before}\n  after:  {after}")

if not raw:
    sys.exit("ABORT — psql returned no JSON. Did the transaction fail?")
data = json.loads(raw[-1])
probes = data["probes"]
config = data["config"]
defaults = {d["market"]: d["city"] for d in data["defaults"]}

by_key = {(p["market"], p["city"], p["query"]): p for p in probes}


def render_state(r):
    """The one state this response renders, per 010 SPEC decision 15's precedence.

    Computed HERE as well as in the component on purpose. The plan calls
    precedence "the easiest thing to implement wrongly and never notice" — six
    bands and an independent `near_empty` flag, so a chip tagged band:confident
    can legitimately have to render the near-empty state. A fixture that only
    carried the band would let that inversion pass silently.
    """
    if r["band"] == "unknown_query":
        return "refusal"
    if r["band"] == "empty":
        return "none"
    if r["band"] == "abstain":
        return "abstain"          # near_empty is impossible here: available is 0
    if r["city_empty"]:
        # Market scored above LOW, this city stocks nothing. 424 of 12,260 combos.
        # No chip reaches it today, which is exactly why it belongs in the fixture:
        # if a threshold moves and one does, this file changes and `fe` sees it.
        return "city_empty"
    if r["near_empty"]:
        return "near_empty"       # overrides confident AND adjacent
    return r["band"]


# -- the band chips: spec-named where the spec names one, else by volume ------
# Cells are filled on RENDER STATE, not on band. `karting` in Paris is band
# `adjacent` but renders near-empty, so letting it fill FR's adjacent cell would
# leave that market with no chip that ever shows the adjacent state — the one the
# purple labelled container exists for.
pinned_keys = {(m, c, q) for m, c, q, _ in PINNED}
covered = {(m, render_state(by_key[(m, c, q)]["r"]))
           for m, c, q in pinned_keys if c == defaults.get(m)}

auto = {}
for m, city in sorted(defaults.items()):
    for band in BANDS:
        if (m, band) in covered:
            continue              # a spec-named chip already fills this cell
        pool = [p for p in probes
                if p["market"] == m and p["city"] == city
                and p["in_qc_pool"] and not p["is_pinned"]
                and render_state(p["r"]) == band]
        if not pool:
            sys.exit(f"ABORT — no logged query in {m} · {city} renders state `{band}`. "
                     f"Criterion 1 wants one chip per market x band and this market cannot "
                     f"supply one; that is a finding about the thresholds, not a fixture bug.")
        pick = max(pool, key=lambda p: (p["searches"], p["query"]))
        auto[(m, city, pick["query"])] = band

# -- the city_empty chip, selected the same way: by volume, never by taste ----
# SPEC criterion 1 wants EVERY state reachable by a named chip, and decision 19
# added a sixth. Without this the only route to city_empty is free text with
# exactly the right market AND city, which nobody guesses. 424 of 12,260 combos
# qualify; the chip is the one the June log searched most in that actual city.
ce_pool = [p for p in probes if p["in_seed_pool"] and p["r"].get("city_empty")]
if not ce_pool:
    sys.exit("ABORT — no seeded (market, city, query) cell returns city_empty. "
             "Criterion 1 then has no chip for the state and free text is the only "
             "route to it; that is a finding about the thresholds, not a fixture bug.")
ce = max(ce_pool, key=lambda p: (p["seed_searches"], p["market"], p["city"], p["query"]))
CITY_EMPTY = (ce["market"], ce["city"], ce["query"])

# -- assemble, merging roles where a chip serves more than one purpose --------
chips = {}


def add(market, city, query, role):
    key = (market, city, query)
    p = by_key.get(key)
    if p is None:
        sys.exit(f"ABORT — {market} · {city} · {query!r} was never probed.")
    r = p["r"]
    if r.get("band") == "unknown_query":
        sys.exit(f"ABORT — {market} · {city} · {query!r} is not in the logged 613, so it would "
                 f"render the refusal card. A chip must not be a refusal; the refusal is "
                 f"reached by typing, which is the honest way to meet it.")
    chip = chips.setdefault(key, {
        "id": f"{market}-{city}-{query}".lower().replace(" ", "-"),
        "market": market, "city": city, "query": query, "roles": [],
        # Everything below is READ OFF THE RPC. None of it is typed.
        "expect": {
            # The state the page must render. Derived from `band` + `near_empty`
            # by the precedence rule, so `fe` asserts on the state it draws.
            "render_state": render_state(r),
            "band": r["band"],
            "near_empty": r["near_empty"],
            "city_empty": r["city_empty"],
            # Read off the RPC, never inferred from the band. The staff panel
            # printed "not written - not an abstention" on city-empty responses
            # precisely because a component re-derived this.
            # DESCRIBES ONE RESPONSE, NOT A RUNNING TOTAL: a second click on the
            # same chip writes a second row, by design. n=1 each, so the seeded
            # month is untouchable either way — but do not assert a demand_events
            # COUNT off this field.
            "demand_row_written": r["demand_row_written"],
            "available": r["available"],
            "result_count": r["result_count"],
            "normalised": r["normalised"],
            "resolved_to": r["resolved_to"],
            "alternatives_above_floor": r["alternatives_above_floor"],
            "alt_max": r["staff"]["alt_max"],
            "part_a_logged_here": r["staff"]["part_a_logged_here"],
            "part_a_class": r["staff"]["part_a_class"],
            "part_a_coverage": r["staff"]["part_a_coverage"],
            "band_agrees_with_part_a": r["staff"]["band_agrees_with_part_a"],
        },
    })
    if role not in chip["roles"]:
        chip["roles"].append(role)
    return r


for (m, c, q), band in auto.items():
    add(m, c, q, f"band:{band}")

for market, city, query, role in list(PINNED) + [CITY_EMPTY + ("city_empty",)]:
    r = add(market, city, query, role)
    if not ROLE_ASSERTS[role](r):
        sys.exit(f"ABORT — {market} · {city} · {query!r} no longer satisfies role `{role}`.\n"
                 f"  band={r['band']} near_empty={r['near_empty']} "
                 f"above_floor={r['alternatives_above_floor']} "
                 f"agrees={r['staff']['band_agrees_with_part_a']} "
                 f"logged_here={r['staff']['part_a_logged_here']} "
                 f"normalised={r['normalised']}\n"
                 f"  The chip set is re-derived from this script, never hand-edited "
                 f"(010 SPEC, 'What would make this spec wrong').")
    # A pinned chip also earns its band tag, so `fe` can filter on band alone.
    tag = f"band:{r['band']}"
    if tag not in chips[(market, city, query)]["roles"]:
        chips[(market, city, query)]["roles"].append(tag)

ordered = sorted(chips.values(), key=lambda c: (BANDS.index(c["expect"]["band"]),
                                                c["market"], c["city"], c["query"]))

# -- coverage assertions ------------------------------------------------------
cells = {(c["market"], c["expect"]["render_state"]) for c in ordered}
missing = {(m, b) for m in defaults for b in BANDS} - cells
if missing:
    sys.exit(f"ABORT — market x state cells with no chip that RENDERS it: {sorted(missing)}")

n_near_empty = sum(1 for c in ordered if "near_empty" in c["roles"])
if n_near_empty != 5:
    sys.exit(f"ABORT — expected 5 near-empty chips, got {n_near_empty}")

# Criterion 1: every state a chip can reach must have one. `refusal` is
# deliberately absent — it is reached by typing, which is the honest way to meet
# it, and a chip that is a refusal would be a chip that never works.
reachable = {c["expect"]["render_state"] for c in ordered}
for state in ("confident", "adjacent", "near_empty", "abstain", "city_empty"):
    if state not in reachable:
        sys.exit(f"ABORT — no chip reaches render state `{state}` (SPEC criterion 1)")

payload = {
    "generated_by": "docs/analysis/010-screens/build_chips.py",
    "generated_on": str(date.today()),
    "spec": "docs/analysis/010-screens/SPEC.md acceptance criteria 1, 2, 3, 6, 7",
    "how": ("Every band and flag under `expect` was read off public.search_deals on the local "
            "database inside a rolled-back transaction. The query strings and cities are curated "
            "(SPEC honesty register); nothing else here is. Re-run the script rather than editing "
            "this file — a hand-edited chip is a chip that claims a state the RPC does not return. "
            "`expect.demand_row_written` describes a single response, not a cumulative count: every "
            "abstain and every city-empty search writes another row (n=1), so assert it against the "
            "RPC's answer, never against a row count."),
    "provenance": {
        "note": ("Recorded so this file can be dated against a calibration. The UI must read "
                 "thresholds from public.search_config at runtime (SPEC G6), never from here."),
        **config,
    },
    "default_city_by_market": defaults,
    "counts": {
        "chips": len(ordered),
        "by_band": {b: sum(1 for c in ordered if c["expect"]["band"] == b) for b in BANDS},
        "by_render_state": {s: sum(1 for c in ordered if c["expect"]["render_state"] == s)
                            for s in sorted({c["expect"]["render_state"] for c in ordered})},
        "near_empty": n_near_empty,
        "states_reachable_by_chip": sorted(reachable),
    },
    "chips": ordered,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

print(f"wrote {OUT.relative_to(ROOT)}  ({len(ordered)} chips)")
print(f"  demand_events unchanged: {before}")
for c in ordered:
    print(f"  {c['expect']['band']:<10} -> {c['expect']['render_state']:<11} "
          f"{c['market']} · {c['city']:<11} {c['query']:<22} "
          f"avail={c['expect']['available']:<3} "
          f"floor={str(c['expect']['alternatives_above_floor']):<5} "
          f"agrees={str(c['expect']['band_agrees_with_part_a']):<5} {','.join(c['roles'])}")
