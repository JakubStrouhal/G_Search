#!/usr/bin/env python3
"""
Groupon case study — the query classifier.

WHY THIS EXISTS. The brief grades "whether the prototype reflects what you found,
rather than being a nice search UI bolted on beside the analysis". The way to
make that true rather than merely claimed is to have the prototype *read* the
analysis. This script emits `outputs/query_classes.csv`: every market+query pair
in the log, assigned to a failure class, with the evidence that put it there.
The prototype's behaviour is keyed to the class column. If the analysis changes,
the prototype changes with it.

THE CLASSES (from PLAN.md §5 — supply reality x system response):

  F1  SILENT SUBSTITUTION  Catalogue stocks nothing answering this, yet results
                           come back anyway. Invisible to every zero-result
                           dashboard. The interesting one.
  F2  LANGUAGE             Catalogue stocks it, but this phrasing fails.
  F3  GEOGRAPHIC           Stocked, fails in some cities and not others.
  F4  SUPPLY VOID          Stocks nothing, and returns nothing. Honest failure.
                           Not a search problem — a merchant acquisition signal.
  F5  RANKING              Stocked, fails intermittently within the same city.
  F6  INTENT-TYPE          Goods/experience confusion. NOT ASSIGNABLE HERE — see
                           note at the bottom. Observed live, cannot occur in
                           this dataset.
  OK                       Stocked, and mostly working.

THE JUDGEMENT CALL, STATED UP FRONT. Deciding whether the catalogue "answers" a
query is not mechanical. The catalogue holds 15 products. `escape room` is
plainly stocked. `paintball` is plainly not. But `pilates` against a deal titled
"Unlimited Fitness Classes" is a judgement, not a fact. So coverage is recorded
in THREE levels — stocked / plausible / absent — and the tier is printed, so a
reader can disagree with a specific call without discarding the classification.
Anyone who thinks `pilates` should be `absent` can move one line and re-run.

Run:  python3 docs/analysis/classify.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_rows", 400)

BRIEF = Path(__file__).resolve().parent.parent / "brief"
OUTPUTS = Path(__file__).resolve().parent / "outputs"
OUTPUTS.mkdir(exist_ok=True)

MIN_N = 10          # below this, classify but flag as thin
DEAD_HI = 0.60      # "this phrasing mostly fails"
DEAD_OK = 0.45      # "this phrasing mostly works"
SPREAD_HI = 0.25    # city-to-city spread that counts as a geography effect

# ---------------------------------------------------------------------------
# 1. Concept map. Hand-built, multilingual. Deliberately NOT LLM-generated —
#    a fabricated map is exactly the thing that cannot be defended in Part C.
# ---------------------------------------------------------------------------
CONCEPTS = {
    "massage":        r"massage|masaż|masaz|masaje|modelage|wellness|spa|nacken|rücken|ruck|espalda|pleców|plecow|dos|tajski|tailandes|thai|sportmassage|descontracturante|paar|pareja|duo|dla par|deep tissue|wohlfühl|entspann|bienestar|détente|relaks",
    "hair":           r"friseur|fryzjer|peluqueria|coiffeur|haircut|hair colour|hair color|haare|färben|farben|tinte|coloration|koloryzacja|strzyż|strzyz|cheveux|pelo|włos|wlos|styling",
    "facial":         r"facial|gesichtsbehandlung|limpieza facial|soin visage|oczyszczanie twarzy|twarz|visage|gesicht",
    "nails":          r"manicure|manicura|maniküre|manikure|manucure|pedicure|pediküre|pedicura|paznok",
    "lashes":         r"wimpern|pestañas|pestanas|cils|rzęs|rzes|eyelash|lash",
    "gym":            r"gym|fitnessstudio|gimnasio|salle de sport|siłownia|silownia|karnet|abonnement|fitness",
    "personaltrain":  r"personal train|personal trainer|entrenador personal|coach sportif|trener personalny|coaching",
    "yoga":           r"yoga|joga",
    "pilates":        r"pilates|plates",
    "crossfit":       r"crossfit|crrossfit|crossfiit",
    # Split deliberately. The catalogue's dining deals are "Three-Course Meal for
    # Two", "Tasting Menu", "Dinner & Wine" — generic sit-down formats. Those
    # answer "menu degustacyjne". They do NOT answer "burger" or "tapas".
    # An earlier version lumped both together and credited the catalogue with
    # stocking cuisines it does not name, which pushed genuinely-absent queries
    # into F3_geographic. Caught in the hand-audit; see LIMITS at the bottom.
    "dining_generic": r"restauracja|restaurant|restaurante|degust|menu|menú|kolacja|cena|dinner|dîner|wine|wein|vin|winem|maridaje",
    # `brunch` belongs here, not in dining_generic. Every dining title in the
    # catalogue is an evening sit-down format — "Three-Course Meal for Two",
    # "Tasting Menu", "Dinner & Wine". Brunch is a different daypart, and
    # crediting it as stocked is the same over-credit as burger and tapas.
    # It was the largest concept in F3_geographic (ES 64, DE 59, PL 35 searches)
    # on exactly that error.
    "dining_specific": r"brunch|italiener|italien|italiana|włoska|wloska|steak|steakhaus|tapas|arroceria|crêperie|creperie|pizzeria|pizza|burger|hamburguesa|indian",
    "sushi":          r"sushi|susshi",
    "bowling":        r"bowling|bolera|kręgle|kregle|bowing|bowlig|kegeln",
    "paintball":      r"paintball|paintballl",
    "escaperoom":     r"escape|escpe",
    "karting":        r"karting|kart fahren|gokarty|go karting|kartbahn",
    "citytour":       r"city tour|stadtrundfahrt|stadtführung|tour ciudad|visite guidee|visite guidée|zwiedzanie|guided city|tour guiado",
    "adrenaline":     r"rafting|raftng|raffting|helikopter|helicopt|helicoptero|hubschrauber|balon|balloon|globo|montgolfiere|montgolfière|heißluft|heissluft|skydiv|parachut|spadochron|fallschirm|fallschirmspringn|supercar|track day|shark|bungee|quad|paracaid|lot balonem",
}

# Terms that LOOK English because they also appear in the GB log, but are the
# ordinary local word in DE/ES/FR/PL too. Treating these as "English phrasing"
# is the exact confound that language_test.py had to design out: they name
# concepts the catalogue does not stock, so they fail for SUPPLY reasons at the
# ordinary rate (44.0%), not for language reasons (81.2%). Excluded from the
# English flag so F2 does not absorb what is really F1/F4.
LOANWORDS = {"brunch", "crossfit", "pilates", "sushi", "paintball", "bowling",
             "escape room", "manicure", "karting", "yoga", "spa", "wellness"}

# ---------------------------------------------------------------------------
# 2. Coverage. Does this market's catalogue hold something that answers it?
#    Three levels, because binary would be dishonest.
#      stocked   — the catalogue names this thing
#      plausible — a generic deal could arguably cover it (judgement, flagged)
#      absent    — nothing in 568 deals answers it
# ---------------------------------------------------------------------------
STOCK_TITLE = {   # concept -> title regex proving the catalogue holds it
    "massage":       r"massage|masaż|masaje|masaz|wellness|spa|modelage|wohlfühl|bienestar|détente|entspannung",
    "hair":          r"hair|haar|coupe|corte|strzy|cheveux",
    "facial":        r"facial|visage|twarz|gesicht",
    "nails":         r"manicure|manicura|maniküre|manucure|pedicure|pediküre",
    "gym":           r"gym|fitness|siłown|gimnasio|salle de sport|karnet|abonnement|pase|mitgliedschaft",
    "personaltrain": r"personal|entrenamiento|trening|coaching",
    "dining_generic": r"menu|menú|meal|dinner|dîner|cena|kolacja|gänge|plats|daniowe|platos|degust|wine|vin|wein|winem|maridaje|tasting",
    "escaperoom":    r"escape",
    "karting":       r"karting|kartbahn|go-kart|kartingowy",
    "citytour":      r"city tour|stadtführung|visite guidée|tour guiado|zwiedzanie|guided city",
}
# Judgement calls: no deal names these, but a generic class deal could cover them.
# Move any of these to `absent` by deleting the line, and re-run.
PLAUSIBLE = {
    "yoga":    "generic 'Unlimited Fitness Classes' could include yoga",
    "pilates": "generic 'Unlimited Fitness Classes' could include pilates",
    "crossfit": "arguable — crossfit is a distinct format, not a generic class",
    "dining_specific": "a generic 'Three-Course Meal' deal could be at an Italian "
                       "or burger place — the catalogue does not say. Credited as "
                       "plausible, never as stocked",
}
# Everything else with no STOCK_TITLE entry is absent by inspection of all 75 titles:
#   lashes, sushi, bowling, paintball, adrenaline

# THE SEAM, LIFTED TO A CONSTANT SO IT CAN BE TESTED RATHER THAN ARGUED.
# `plausible` is the one genuinely contestable tier, and the whole inventory-location
# headline swings on it: 844 dead ends move together. Three defensible readings:
#
#   "cant_tell"       the honest one, and the default. We do not know, so we say so
#                     and neither side of the argument gets to count them.
#   "nowhere"         treat a generic deal as no answer at all -> NOWHERE 63.4%
#   "stocked_generic" credit it against the generic proxy below -> NOWHERE 44.8%
#
# Section 3b prints all three. Nothing downstream may quote one without the band.
PLAUSIBLE_COUNTS_AS = "cant_tell"

# Only used by the "stocked_generic" sensitivity arm — never by the default path.
GENERIC_PROXY = {
    "yoga":            STOCK_TITLE["gym"],
    "pilates":         STOCK_TITLE["gym"],
    "crossfit":        STOCK_TITLE["gym"],
    "dining_specific": STOCK_TITLE["dining_generic"],
}

searches = pd.read_csv(BRIEF / "search_log.csv")
deals = pd.read_csv(BRIEF / "deals.csv")
searches["zero"] = (searches["results_shown"] == 0).astype(int)
searches["dead"] = (searches["results_shown"] <= 2).astype(int)
searches["q"] = searches["raw_query"].str.lower().str.strip()

GB_QUERIES = set(searches[searches["market"] == "GB"]["q"].unique())


def concept_of(q):
    hits = [c for c, pat in CONCEPTS.items() if pd.Series([q]).str.contains(pat, regex=True)[0]]
    if not hits:
        return "unmapped"
    # adrenaline and specific foods win over generic buckets when both match
    for pref in ("adrenaline", "sushi", "paintball", "bowling", "escaperoom",
                 "karting", "citytour", "crossfit", "pilates", "yoga",
                 "dining_specific"):
        if pref in hits:
            return pref
    return hits[0]


searches["concept"] = searches["q"].map(concept_of)


def coverage(market, concept, city=None):
    """Does this market's catalogue hold something answering `concept`?

    `city=None` is the market-grain test the classifier has always used, and its
    result is unchanged. Passing a city narrows the same test to that city, which
    is what section 3b needs to ask *where* the answer was.
    """
    pat = STOCK_TITLE.get(concept)
    if pat:
        sub = deals[deals["market"] == market]
        if city is not None:
            sub = sub[sub["city"] == city]
        n = int(sub["title"].str.lower().str.contains(pat, regex=True, na=False).sum())
        if n:
            return "stocked", n
    if concept in PLAUSIBLE:
        return "plausible", 0
    return "absent", 0


# ---------------------------------------------------------------------------
# 3. Per market+query aggregation, then the rules.
# ---------------------------------------------------------------------------
g = searches.groupby(["market", "q"]).agg(
    searches=("dead", "size"), zeros=("zero", "sum"), deads=("dead", "sum"),
    clicks=("clicked", "sum"), buys=("purchased", "sum"),
    concept=("concept", "first"),
).reset_index()
g["zero_rate"] = g["zeros"] / g["searches"]
g["dead_rate"] = g["deads"] / g["searches"]

city = searches.groupby(["market", "q", "city"]).agg(n=("dead", "size"), d=("dead", "mean")).reset_index()
spread = city[city["n"] >= 3].groupby(["market", "q"])["d"].agg(lambda x: x.max() - x.min())
g["city_spread"] = g.set_index(["market", "q"]).index.map(spread).astype(float)

cov = [coverage(m, c) for m, c in zip(g["market"], g["concept"])]
g["coverage"] = [c[0] for c in cov]
g["deals_stocking"] = [c[1] for c in cov]
g["is_english"] = ((g["market"] != "GB") & g["q"].isin(GB_QUERIES)
                   & ~g["q"].isin(LOANWORDS))


def classify(r):
    # Nothing in the catalogue answers it.
    if r["coverage"] == "absent":
        # Honest failure vs confident wrong answer — the whole F1/F4 distinction.
        return "F4_supply_void" if r["zero_rate"] >= 0.5 else "F1_silent_substitution"
    # Catalogue holds it. So why is it failing?
    if r["dead_rate"] < DEAD_OK:
        # NOT "fine". The best-performing stocked queries still dead-end ~40% of
        # the time, because 1-2 results is so common. This is the floor the whole
        # platform sits on, not a clean bill of health.
        return "BASELINE_still_40pct_dead"
    if r["is_english"]:
        return "F2_language"
    if not np.isnan(r["city_spread"]) and r["city_spread"] >= SPREAD_HI:
        return "F3_geographic"
    if r["dead_rate"] >= DEAD_HI:
        return "F5_ranking"
    return "F5_ranking"


g["failure_class"] = g.apply(classify, axis=1)
g["thin_n"] = g["searches"] < MIN_N
g = g.sort_values("deads", ascending=False)


# ---------------------------------------------------------------------------
# 3b. INVENTORY LOCATION — "when the search failed, where was the answer?"
#
#     The classifier above asks WHY a query failed. This asks WHERE the answer
#     was, which is the question a non-analyst can hold, and it partitions the
#     same dead ends into four buckets with four different owners:
#
#       same_city     stocked in the user's own city, and search still failed
#       another_city  stocked in the market, never where the user was
#       nowhere       nothing in this market's catalogue answers it, ever
#       cant_tell     a generic deal might or might not answer it, or we could
#                     not map the query to a concept at all
#
#     This is `coverage()` evaluated at (market, city) instead of (market), so
#     it introduces no new judgement beyond the PLAUSIBLE_COUNTS_AS seam above.
#     Deliberately NOT put in validate.py: that file carries a second, coarser
#     CONCEPTS map, and computing this there would produce a third number for
#     one claim from a third map (known issues #1/#2 are exactly that shape).
# ---------------------------------------------------------------------------

def _stock_index(stock_map):
    """Sets of (concept, market, city) and (concept, market) with a title match.

    Precomputed rather than tested per row — the per-row version is the same
    answer several hundred thousand regex evaluations more slowly.
    """
    titles = deals["title"].str.lower()
    city_hit, market_hit = set(), set()
    for concept, pat in stock_map.items():
        m = titles.str.contains(pat, regex=True, na=False)
        if not m.any():
            continue
        hit = deals[m]
        city_hit |= {(concept, mk, ct) for mk, ct in zip(hit["market"], hit["city"])}
        market_hit |= {(concept, mk) for mk in hit["market"]}
    return city_hit, market_hit


def locate(concept_col, plausible_as):
    """Assign every search row a bucket under one seam convention."""
    stock_map = dict(STOCK_TITLE)
    if plausible_as == "stocked_generic":
        stock_map.update(GENERIC_PROXY)
    city_hit, market_hit = _stock_index(stock_map)
    fallback = "cant_tell" if plausible_as == "cant_tell" else "nowhere"

    out = []
    for con, mk, ct in zip(concept_col, searches["market"], searches["city"]):
        if con == "unmapped":
            # Not "we know we don't stock it" — we don't know what was asked.
            # All 172 dead ends here are typos at n<=2 (known issue #8).
            out.append("cant_tell" if plausible_as == "cant_tell" else "nowhere")
        elif (con, mk, ct) in city_hit:
            out.append("same_city")
        elif (con, mk) in market_hit:
            out.append("another_city")
        elif con in PLAUSIBLE:
            out.append(fallback)
        else:
            out.append("nowhere")
    return pd.Series(out, index=searches.index)


BUCKETS = ["nowhere", "same_city", "another_city", "cant_tell"]
searches["inventory_location"] = locate(searches["concept"], PLAUSIBLE_COUNTS_AS)

# Fold the per-search buckets back onto the (market, q) grain. Additive integer
# columns only: query_classes.csv MUST stay keyed (market, q) because both
# consumers -- 002-recoverability and 004-data-story -- join on that index and a
# duplicated index raises rather than warns.
dead_rows = searches[searches["dead"] == 1]
loc_counts = (dead_rows.groupby(["market", "q", "inventory_location"]).size()
              .unstack(fill_value=0).reindex(columns=BUCKETS, fill_value=0))
for b in BUCKETS:
    g[f"dead_{b}"] = (g.set_index(["market", "q"]).index
                      .map(loc_counts[b]).fillna(0).astype(int))

# THE INVARIANT. If a future edit to CONCEPTS, STOCK_TITLE or PLAUSIBLE breaks
# the partition, fail here rather than emit a fifth number for one claim.
_sum = g[[f"dead_{b}" for b in BUCKETS]].sum(axis=1)
assert (_sum == g["deads"]).all(), (
    "inventory-location buckets do not partition `deads` on "
    f"{int((_sum != g['deads']).sum())} rows — the decomposition is broken"
)
assert set(searches.loc[searches["dead"] == 1, "inventory_location"]) <= set(BUCKETS)

print("=" * 100)
print("QUERY CLASSIFICATION — every market+query pair in the log")
print("=" * 100)
summary = g.groupby("failure_class").agg(
    pairs=("searches", "size"), searches=("searches", "sum"),
    dead_ends=("deads", "sum"), zeros=("zeros", "sum")).sort_values("dead_ends", ascending=False)
summary["share_of_all_dead_ends"] = summary["dead_ends"] / g["deads"].sum()
print(summary.round(3).to_string())

print(f"\nunmapped concepts: {(g['concept'] == 'unmapped').sum()} pairs, "
      f"{g[g['concept'] == 'unmapped']['searches'].sum()} searches "
      f"({g[g['concept'] == 'unmapped']['searches'].sum() / g['searches'].sum():.1%})")

print("\nCOVERAGE TIER (the judgement calls are the 'plausible' row):")
print(g.groupby("coverage").agg(pairs=("searches", "size"), searches=("searches", "sum"),
                                dead_rate=("dead_rate", "mean")).round(3).to_string())

# ---------------------------------------------------------------------------
print("\n" + "=" * 100)
print("INVENTORY LOCATION — when the search failed, where was the answer?")
print("=" * 100)

TOTAL_DEAD = int(g["deads"].sum())
OWNER = {
    "nowhere":      "nothing in this market answers it, ever   -> MERCHANT ACQUISITION",
    "same_city":    "stocked in the user's own city, missed    -> SEARCH",
    "another_city": "in the market, never where the user is    -> product/UX",
    "cant_tell":    "a generic deal might answer it; unmapped  -> NOT ATTRIBUTED",
}
for b in BUCKETS:
    n = int(g[f"dead_{b}"].sum())
    print(f"  {b:<13}{n:>6,}  {n / TOTAL_DEAD * 100:5.1f}%   {OWNER[b]}")
print(f"  {'TOTAL':<13}{TOTAL_DEAD:>6,}  100.0%")

print("\n  cross-tab against the failure classes (they nest — 'nowhere' is F1 + F4):")
print(pd.crosstab(searches.loc[searches["dead"] == 1, "inventory_location"],
                  searches.loc[searches["dead"] == 1].set_index(["market", "q"])
                  .index.map(g.set_index(["market", "q"])["failure_class"]))
      .reindex(BUCKETS).to_string())

print(f"""
  THE SEAM, QUANTIFIED. `plausible` is the one contestable tier and all of its
  dead ends move together. Currently PLAUSIBLE_COUNTS_AS = {PLAUSIBLE_COUNTS_AS!r}.
  Shares below are of all {TOTAL_DEAD:,} dead ends, one denominator throughout:""")

sens = {}
for conv in ("cant_tell", "nowhere", "stocked_generic"):
    loc = locate(searches["concept"], conv)
    v = loc[searches["dead"] == 1].value_counts()
    sens[conv] = {b: int(v.get(b, 0)) for b in BUCKETS}
    row = "  ".join(f"{b} {sens[conv][b] / TOTAL_DEAD * 100:5.1f}%" for b in BUCKETS)
    print(f"    {conv:<16} {row}")
print(f"""
    => NOWHERE spans [{sens['stocked_generic']['nowhere'] / TOTAL_DEAD * 100:.1f}%,"""
      f" {sens['nowhere']['nowhere'] / TOTAL_DEAD * 100:.1f}%] across the three readings."
      "\n       Quote the band, never one end alone.")

print("\n  per-concept contribution of the seam (dispute one line and re-run):")
for con in sorted(PLAUSIBLE):
    n = int(dead_rows[dead_rows["concept"] == con].shape[0])
    print(f"    {con:<18}{n:>5} dead ends   — {PLAUSIBLE[con]}")

# ---------------------------------------------------------------------------
# 4. THE FIX LIST — this is the artifact a PM actually ships.
# ---------------------------------------------------------------------------
print("\n" + "=" * 100)
print("THE FIX LIST — top 30 market+query pairs by dead-ends caused")
print("=" * 100)
fix = g.head(30)[["market", "q", "concept", "searches", "deads", "dead_rate",
                  "coverage", "failure_class"]]
print(fix.round(3).to_string(index=False))
cum = g["deads"].cumsum() / g["deads"].sum()
for k in (10, 25, 50, 100):
    if k <= len(g):
        print(f"top {k:>3} pairs = {cum.iloc[k-1]:.1%} of all dead-ends")

g.to_csv(OUTPUTS / "query_classes.csv", index=False)
fix.to_csv(OUTPUTS / "fix_list.csv", index=False)

# City grain, for anything that needs to know WHICH city — the Part B staff panel
# and the acquisition list. Kept out of query_classes.csv on purpose: that file is
# the (market, q) contract and must not grow a duplicated index.
inv = (searches.groupby(["market", "city", "q", "concept", "inventory_location"])
       .agg(searches=("dead", "size"), deads=("dead", "sum"),
            zeros=("zero", "sum"), buys=("purchased", "sum"))
       .reset_index().sort_values("deads", ascending=False))
inv.to_csv(OUTPUTS / "inventory_location.csv", index=False)

# The seam band, emitted rather than quoted. 004-data-story reads this so the
# explainer's sensitivity line cannot drift from the script that computed it.
(pd.DataFrame(sens).T.reindex(columns=BUCKETS)
 .rename_axis("plausible_counts_as").reset_index()
 .assign(is_default=lambda x: x.plausible_counts_as == PLAUSIBLE_COUNTS_AS,
         total_dead=TOTAL_DEAD)
 .to_csv(OUTPUTS / "inventory_sensitivity.csv", index=False))

print(f"\nwritten: {OUTPUTS / 'query_classes.csv'}  ({len(g)} rows — the Part A→B contract)")
print(f"written: {OUTPUTS / 'fix_list.csv'}")
print(f"written: {OUTPUTS / 'inventory_location.csv'}  ({len(inv)} rows — market x city x query)")

print("""
HAND-AUDIT — 2026-08-05, 35 non-thin rows (n>=10), 6 per class, seed 7

  F4_supply_void          6/6  unambiguous. Absent concept, 100% zero.
  F1_silent_substitution  6/6  paintball, bowling, sushi, bolera, eyelash ext.
                               All genuinely absent from 568 deals; all return
                               results. Correct by construction.
  BASELINE                6/6  stocked, 26-44% dead.
  F5_ranking              5/6  one rests on a `plausible` coverage call (pilates).
  F2_language             4/5  `thai massage` in DE is borderline — arguably a
                               German loanword rather than English phrasing.
  F3_geographic           3/6  FAILED. Systematic, not random: the concept map
                               credited a generic "Three-Course Meal for Two"
                               with answering `burger`, `tapas`, `brunch`. It
                               does not.

  => ~86% agreement before the fix. The F3 failure was a CAUSE, not a symptom,
     so it was fixed rather than noted: `dining_specific` (brunch, burger, tapas,
     pizza, steak, indian, italian) is now split from `dining_generic` and can
     never be credited as `stocked` — only `plausible`. Re-running moved 45
     pairs / 1,090 searches out of `stocked`. F3 is now 8 stocked + 7 plausible,
     with the tier visible in every row so the judgement can be disputed.

     `brunch` needed a second pass. The first fix moved the cuisines but left
     brunch in `dining_generic`, and brunch was the LARGEST concept in F3 (ES 64,
     DE 59, PL 35). Every dining title in the catalogue is an evening sit-down
     format; brunch is a different daypart. Same over-credit, missed once.

  This number is a self-audit by the same author who wrote the rules, which is
  the weakest form of validation. Treat ~86% as an upper bound.

LIMITS OF THIS CLASSIFICATION — read before quoting it
  - F1 vs F4 is split on whether results came back, NOT on whether those results
    were relevant. The log records `results_shown` as a bare count with no
    query→deal mapping, so "these users saw the wrong thing" is inference from
    the coverage tier, never observation. F1's SIZE here is the size of a
    coverage gap that still returns results — not a measurement of user harm.
  - F6 (goods vs experience intent) is NOT ASSIGNED. It was observed live —
    `shark` returns shark blankets on groupon.co.uk — but this catalogue contains
    no Goods at all, so the failure cannot occur in this dataset. Forcing rows
    into it would be inventing a finding.
  - `plausible` coverage is a judgement, not a measurement. It is printed
    separately so the classification survives someone disagreeing with it.
  - Thin rows (n < 10) are classified but flagged in `thin_n`.
""")
