#!/usr/bin/env python3
"""
Groupon case study — validation harness.

Purpose: do NOT take any headline number on trust. Every claim in Part A
should come out of this file, with its own counts attached, so that if the
hiring manager asks "how do you know", the answer is a line number.

Run:  python validate.py
Requires: pandas, numpy
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 200)

# Paths resolve against this file, not the working directory, so the script runs
# from anywhere. The CSVs live in docs/brief/ and are treated as immutable input —
# nothing here writes back to them.
BRIEF = Path(__file__).resolve().parent.parent / "brief"
OUTPUTS = Path(__file__).resolve().parent / "outputs"

SEARCH_PATH = BRIEF / "search_log.csv"
DEALS_PATH = BRIEF / "deals.csv"

MIN_N = 30  # below this, report the count and refuse to report a rate


def rule(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------------------
# LAYER 0 — shape and integrity. Trust nothing until this passes.
# ---------------------------------------------------------------------------

searches = pd.read_csv(SEARCH_PATH)
deals = pd.read_csv(DEALS_PATH)

rule("LAYER 0 — data shape and integrity")

print(f"searches: {searches.shape[0]} rows, {searches.shape[1]} cols")
print(f"deals:    {deals.shape[0]} rows, {deals.shape[1]} cols")

def show_nulls(df, name):
    n = df.isna().sum()
    n = n[n > 0]
    print(f"\nnulls ({name}):")
    print(n.to_string() if len(n) else "  none")

show_nulls(searches, "searches")
show_nulls(deals, "deals")

print(f"\nduplicate query_id: {searches['query_id'].duplicated().sum()}")
print(f"duplicate deal_id:  {deals['deal_id'].duplicated().sum()}")

searches["date"] = pd.to_datetime(searches["date"])
print(f"\ndate range: {searches['date'].min().date()} -> {searches['date'].max().date()}")
print(f"days covered: {searches['date'].dt.date.nunique()}")

# Do the two files agree on the world? A market/city in searches with no
# deals at all is a different animal from one with thin deals.
s_mc = set(zip(searches["market"], searches["city"]))
d_mc = set(zip(deals["market"], deals["city"]))
print(f"\nmarket/city in searches but NOT in deals: {sorted(s_mc - d_mc)}")
print(f"market/city in deals but NOT in searches: {sorted(d_mc - s_mc)}")

# Funnel logic integrity: can a row purchase without clicking? click with 0 results?
bad_click = searches[(searches["results_shown"] == 0) & (searches["clicked"] == 1)]
bad_buy = searches[(searches["clicked"] == 0) & (searches["purchased"] == 1)]
print(f"\nIMPOSSIBLE rows — clicked with zero results: {len(bad_click)}")
print(f"IMPOSSIBLE rows — purchased without click:   {len(bad_buy)}")

print("\nresults_shown distribution:")
print(searches["results_shown"].describe())
print("\nvalue counts (top 15):")
print(searches["results_shown"].value_counts().head(15))


# ---------------------------------------------------------------------------
# LAYER 1 — the headline, with its uncertainty attached.
# ---------------------------------------------------------------------------

rule("LAYER 1 — zero-result rate, by market and by city")

searches["zero"] = (searches["results_shown"] == 0).astype(int)

overall = searches["zero"].mean()
print(f"OVERALL zero-result rate: {overall:.1%}  ({searches['zero'].sum()} of {len(searches)})")


def wilson(k, n, z=1.96):
    """Wilson score interval. Use this instead of eyeballing — it stops you
    reporting '33%' off the back of 21 searches."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z**2 / n
    c = p + z**2 / (2 * n)
    m = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return ((c - m) / d, (c + m) / d)


def rate_table(df, keys):
    g = df.groupby(keys).agg(searches=("zero", "size"), zeros=("zero", "sum"))
    g["rate"] = g["zeros"] / g["searches"]
    ci = g.apply(lambda r: wilson(r["zeros"], r["searches"]), axis=1)
    g["ci_lo"] = [c[0] for c in ci]
    g["ci_hi"] = [c[1] for c in ci]
    g["thin"] = g["searches"] < MIN_N
    return g.sort_values("rate", ascending=False)


print("\nBY MARKET:")
print(rate_table(searches, ["market"]).round(3))

print("\nBY MARKET + CITY:")
print(rate_table(searches, ["market", "city"]).round(3))

# The falsification test: do the market confidence intervals overlap?
# If they do, "PL is worse than DE" is a story, not a finding.
print("\nOverlap check — if market CIs overlap, do NOT claim one market is worse.")

# Is the problem drifting over the month, or flat? A trend changes the diagnosis.
print("\nBY WEEK:")
wk = searches.copy()
wk["week"] = wk["date"].dt.isocalendar().week
print(rate_table(wk, ["week"])[["searches", "zeros", "rate"]].round(3).sort_index())


# ---------------------------------------------------------------------------
# LAYER 1b — zero is not the only failure state. Check the shape of the
# results_shown distribution BEFORE accepting "zero results" as the problem.
# ---------------------------------------------------------------------------

rule("LAYER 1b — thin result sets, and a gap in the distribution")

dist = searches["results_shown"].value_counts().sort_index()
print(dist.head(15).to_string())
missing = [k for k in range(0, int(dist.index.max())) if k not in dist.index]
print(f"\nresult counts that NEVER occur below the max: {missing}")
print("A gap here is either a ranking cut-off or a synthetic-data artifact.")
print("Say which you think it is, and say you cannot tell from this file alone.")

nzz = searches[searches["results_shown"] > 0].copy()
nzz["depth"] = pd.cut(nzz["results_shown"], [0, 2, 1000], labels=["1-2", "4+"])
print("\nOutcome by depth — the cliff:")
print(nzz.groupby("depth", observed=True).agg(
    searches=("clicked", "size"), ctr=("clicked", "mean"),
    s2p=("purchased", "mean")).round(3))

thin_n = (searches["results_shown"].between(1, 2)).sum()
zero_n = int(searches["zero"].sum())
print(f"\nzero results:        {zero_n} ({zero_n/len(searches):.1%})")
print(f"1-2 results:         {thin_n} ({thin_n/len(searches):.1%})")
print(f"COMBINED dead-end:   {zero_n+thin_n} ({(zero_n+thin_n)/len(searches):.1%})")
print("\nIf 1-2 results convert like zero, the headline is the combined number,")
print("not the zero-result rate. Check this before writing Part A.")


# ---------------------------------------------------------------------------
# LAYER 2 — the split that matters: always-zero vs sometimes-zero.
# ---------------------------------------------------------------------------

rule("LAYER 2 — always-zero (supply void) vs sometimes-zero (thinness/matching)")


def norm(q):
    q = str(q).lower().strip()
    q = re.sub(r"\s+", " ", q)
    q = re.sub(r"[^\w\s]", "", q)
    return q


searches["q"] = searches["raw_query"].map(norm)

pair = searches.groupby(["market", "q"]).agg(
    n=("zero", "size"), zeros=("zero", "sum"), clicks=("clicked", "sum"),
    buys=("purchased", "sum")
)
pair["zero_rate"] = pair["zeros"] / pair["n"]

pair["bucket"] = np.select(
    [pair["zero_rate"] == 1.0, pair["zero_rate"] == 0.0],
    ["always_zero", "never_zero"],
    default="intermittent",
)

print("\nMARKET+QUERY PAIRS by bucket:")
print(pair.groupby("bucket").agg(pairs=("n", "size"), searches=("n", "sum"),
                                 zeros=("zeros", "sum")))

tot_zeros = pair["zeros"].sum()
print("\nSHARE OF ALL ZERO-RESULT SEARCHES:")
share = pair.groupby("bucket")["zeros"].sum() / tot_zeros
print((share * 100).round(1).to_string())

print("\nTOP 25 ALWAYS-ZERO pairs by lost search volume:")
print(pair[pair["bucket"] == "always_zero"].sort_values("n", ascending=False)
      .head(25)[["n", "zero_rate"]])

print("\nTOP 25 INTERMITTENT pairs by lost searches:")
print(pair[pair["bucket"] == "intermittent"].sort_values("zeros", ascending=False)
      .head(25)[["n", "zeros", "zero_rate"]])

# Is intermittency explained by CITY? That's the falsifiable version of
# "it's supply thinness". If a query is 0% zero in one city and 40% in
# another within the same market, the market-level number is hiding it.
rule("LAYER 2b — is intermittency a CITY effect?")

city_pair = searches.groupby(["market", "q", "city"]).agg(
    n=("zero", "size"), zeros=("zero", "sum")
)
city_pair["zero_rate"] = city_pair["zeros"] / city_pair["n"]

inter_idx = pair[pair["bucket"] == "intermittent"].index
spread = []
for (m, q) in inter_idx:
    sub = city_pair.loc[(m, q)]
    if len(sub) > 1 and sub["n"].min() >= 5:
        spread.append({
            "market": m, "query": q, "searches": int(sub["n"].sum()),
            "min_city_rate": sub["zero_rate"].min(),
            "max_city_rate": sub["zero_rate"].max(),
            "spread": sub["zero_rate"].max() - sub["zero_rate"].min(),
        })
sp = pd.DataFrame(spread).sort_values("spread", ascending=False)
print("\nIntermittent pairs with the widest city-to-city spread:")
print(sp.head(20).round(3).to_string(index=False))
print(f"\nmedian city spread across intermittent pairs: {sp['spread'].median():.3f}")
print("If this median is near zero, city is NOT the explanation — look at")
print("query phrasing or a ranking threshold instead.")


# ---------------------------------------------------------------------------
# LAYER 3 — prove the vocabulary mismatch instead of asserting it.
# ---------------------------------------------------------------------------

rule("LAYER 3 — vocabulary mismatch: is the supply actually there?")

# The test: for a query that returns zero, does the market hold deals in a
# category that a human would say answers it? If yes -> matcher failure.
# If no -> genuine supply void. This is the line between the two buckets,
# and it must be argued explicitly, not assumed.

print("\nInventory the matcher is working against:")
print(deals.groupby(["market"]).agg(deals=("deal_id", "size"),
                                    cities=("city", "nunique")))
print("\nCATEGORY COVERAGE (this is the whole story of the supply void):")
print(pd.crosstab(deals["category_l1"], deals["market"], margins=True))
print()
print(pd.crosstab(deals["category_l2"], deals["market"], margins=True))

# Concept map: hand-built, deliberately. State it as a judgement call in
# Part C — an LLM-generated map would be a fabrication risk you can't defend.
CONCEPTS = {
    "massage": ["massage", "masaz", "masaż", "masaje", "masszazs", "thai massage",
                "masaz tajski", "masaż tajski", "massage thai", "wellness"],
    "beauty": ["hair", "haare", "cheveux", "pelo", "wlosy", "nails", "lashes",
               "eyelash", "cils", "pestanas", "farben", "colour", "color"],
    "fitness": ["gym", "yoga", "pilates", "fitness", "crossfit", "climbing"],
    "dining": ["dinner", "restaurant", "brunch", "tasting", "wine", "essen"],
    "adrenaline": ["rafting", "skydiv", "fallschirm", "helicopter", "hubschrauber",
                   "balloon", "ballon", "supercar", "track day", "shark", "bungee",
                   "paintball", "karting", "quad", "parachut", "saut"],
}


def concept_of(q):
    hits = [c for c, kws in CONCEPTS.items() if any(k in q for k in kws)]
    return hits[0] if len(hits) == 1 else ("|".join(hits) if hits else "unmapped")


pair_r = pair.reset_index()
pair_r["concept"] = pair_r["q"].map(concept_of)

print("\nZERO-RESULT SEARCHES BY CONCEPT (all markets):")
cz = pair_r.groupby("concept").agg(searches=("n", "sum"), zeros=("zeros", "sum"))
cz["zero_rate"] = cz["zeros"] / cz["searches"]
cz["share_of_all_zeros"] = cz["zeros"] / tot_zeros
print(cz.sort_values("zeros", ascending=False).round(3))

print("\nUNMAPPED zero-heavy queries — extend the concept map until this is small:")
print(pair_r[(pair_r["concept"] == "unmapped") & (pair_r["zeros"] > 0)]
      .sort_values("zeros", ascending=False).head(30)[["market", "q", "n", "zeros"]]
      .to_string(index=False))

# The decisive test. For each market x concept: does the catalogue actually STOCK
# something that answers it?
#
# CORRECTED. An earlier version mapped concepts to L2 categories and asked
# "does the category exist". That is the wrong question and it produced a wrong
# answer: adrenaline mapped to `activities`, `activities` has 132 deals, so the
# table printed "MATCHER FAILURE" for skydiving. But `activities` stocks exactly
# three things — escape rooms, karting and guided city tours — and none of them
# is a helicopter. A category that EXISTS is not a category that STOCKS THE THING.
#
# So the test is run at title level. The catalogue is only 75 unique titles =
# 15 distinct products repeated across 5 languages, so this is enumerable rather
# than fuzzy. A concept with no pattern here is stocked NOWHERE, by inspection.
STOCK_PATTERNS = {
    "massage": r"massage|masaż|masaje|masaz|wellness|spa|modelage|wohlfühl|bienestar|détente|entspannung",
    "beauty": r"hair|haar|coupe|corte|strzy|facial|visage|twarz|gesicht|manicure|manicura|maniküre|manucure|pedicure|pediküre",
    "fitness": r"gym|fitness|siłown|gimnasio|salle de sport|personal|entrenamiento|trening|coaching|illimité|ilimitad|unlimited|unbegrenzt|zajęcia|karnet|abonnement|pase|mitgliedschaft",
    "dining": r"menu|menú|meal|dinner|dîner|cena|kolacja|gänge|plats|daniowe|platos|degust|wine|vin|wein|winem|maridaje|tasting",
    # `activities` decomposed into what it actually holds:
    "escape_room": r"escape",
    "karting": r"karting|kartbahn|go-kart|kartingowy",
    "city_tour": r"city tour|stadtführung|visite guidée|tour guiado|zwiedzanie|guided city",
    # adrenaline is deliberately ABSENT — no title in any market matches aerial,
    # water or motorsport. That absence is the finding.
}


def stock_count(market, concept):
    """Deals in `market` whose TITLE indicates it answers `concept`."""
    pat = STOCK_PATTERNS.get(concept)
    if pat is None:
        return 0
    sub = deals[deals["market"] == market]
    return int(sub["title"].str.lower().str.contains(pat, regex=True, na=False).sum())


rows = []
for (m, c), g in pair_r.groupby(["market", "concept"]):
    if c == "unmapped" or "|" in c:
        continue
    stock = stock_count(m, c)
    zeros = int(g["zeros"].sum())
    rows.append({
        "market": m, "concept": c,
        "searches": int(g["n"].sum()), "zeros": zeros,
        "zero_rate": zeros / g["n"].sum(),
        "deals_stocking_it": stock,
        "verdict": "SUPPLY VOID" if stock == 0 else
                   ("MATCHER FAILURE" if zeros > 0 else "ok"),
    })
verdict = pd.DataFrame(rows).sort_values(["verdict", "zeros"], ascending=[True, False])
print("\nDECISIVE TABLE — supply void vs matcher failure, per market x concept:")
print("(stock measured at TITLE level, not category level — see comment above)")
print(verdict.round(3).to_string(index=False))

print("\nWHAT THE CATALOGUE ACTUALLY STOCKS — 15 products, 5 languages:")
prod = deals.copy()
prod["product"] = "other"
for c, pat in STOCK_PATTERNS.items():
    hit = prod["title"].str.lower().str.contains(pat, regex=True, na=False)
    prod.loc[hit & (prod["product"] == "other"), "product"] = c
print(pd.crosstab(prod["product"], prod["market"], margins=True))
print("\nEvery deal falls into one of these. There is no aerial, no water sport,")
print("no motorsport, no paintball, no bowling, no sushi — anywhere, in any market.")

# Same-concept, cross-language proof. If a Polish phrasing dies where the
# English phrasing survives IN THE SAME MARKET, language is the variable.
rule("LAYER 3b — same concept, different phrasing, same market")
for m in sorted(searches["market"].unique()):
    sub = pair_r[(pair_r["market"] == m) & (pair_r["concept"] != "unmapped")]
    for c in sub["concept"].unique():
        cc = sub[sub["concept"] == c].sort_values("zero_rate", ascending=False)
        if cc["zero_rate"].max() > 0.5 and cc["zero_rate"].min() < 0.1:
            print(f"\n{m} / {c}:")
            print(cc[["q", "n", "zeros", "zero_rate"]].round(2).to_string(index=False))


# ---------------------------------------------------------------------------
# LAYER 4 — typos, separately. Small, but cheap to fix, so size it honestly.
# ---------------------------------------------------------------------------

rule("LAYER 4 — near-miss / typo queries")

from difflib import SequenceMatcher

healthy = set(pair_r[pair_r["zero_rate"] < 0.2]["q"])
zeroq = pair_r[pair_r["zero_rate"] == 1.0]

near = []
for _, r in zeroq.iterrows():
    best, score = None, 0
    for h in healthy:
        s = SequenceMatcher(None, r["q"], h).ratio()
        if s > score:
            best, score = h, s
    if score >= 0.85:
        near.append({"market": r["market"], "query": r["q"], "n": int(r["n"]),
                     "closest_healthy": best, "similarity": round(score, 3)})
nr = pd.DataFrame(near).sort_values("n", ascending=False)
print(nr.to_string(index=False) if len(nr) else "none found at 0.85 threshold")
if len(nr):
    print(f"\ntypo-attributable lost searches: {nr['n'].sum()} "
          f"({nr['n'].sum()/tot_zeros:.1%} of all zeros)")


# ---------------------------------------------------------------------------
# LAYER 5 — size the prize. Not all zeros are worth the same.
# ---------------------------------------------------------------------------

rule("LAYER 5 — what is each bucket actually worth?")

nz = searches[searches["results_shown"] > 0]
ctr = nz["clicked"].mean()
cvr = nz[nz["clicked"] == 1]["purchased"].mean()
print(f"When results exist: CTR {ctr:.1%}, click->purchase {cvr:.1%}, "
      f"search->purchase {nz['purchased'].mean():.1%}")

print("\nFunnel by market (non-zero searches only):")
print(nz.groupby("market").agg(searches=("clicked", "size"), ctr=("clicked", "mean"),
                               s2p=("purchased", "mean")).round(3))

# Does having MORE results help, or is there a plateau? This tells you whether
# 'return something' is enough, or whether depth matters.
print("\nOutcome by results_shown bucket:")
nzb = nz.copy()
nzb["bucket"] = pd.cut(nzb["results_shown"], [0, 1, 2, 3, 5, 10, 1000],
                       labels=["1", "2", "3", "4-5", "6-10", "10+"])
print(nzb.groupby("bucket", observed=True).agg(
    searches=("clicked", "size"), ctr=("clicked", "mean"),
    s2p=("purchased", "mean")).round(3))

print("\nRECOVERABLE DEMAND if each bucket converted at the observed rate:")
for b in ["always_zero", "intermittent"]:
    z = int(pair[pair["bucket"] == b]["zeros"].sum())
    print(f"  {b:<14} {z:>5} lost searches -> "
          f"~{z * nz['purchased'].mean():.0f} purchases at current s2p")
print("\nNOTE: this is an UPPER BOUND and should be labelled as such. Recovered")
print("searches convert worse than organic ones. Do not present it as a forecast.")

# Supply density vs outcome — Groupon's own stated mechanism, tested here.
rule("LAYER 5b — does supply density predict outcomes?")
dens = deals.groupby(["market", "city"]).size().rename("deals").reset_index()
perf = searches.groupby(["market", "city"]).agg(
    searches=("zero", "size"), zero_rate=("zero", "mean"),
    s2p=("purchased", "mean")).reset_index()
mm = dens.merge(perf, on=["market", "city"])
print(mm.round(3).sort_values("deals").to_string(index=False))
print(f"\ncorr(deals, zero_rate) = {mm['deals'].corr(mm['zero_rate']):.3f}")
print(f"corr(deals, s2p)       = {mm['deals'].corr(mm['s2p']):.3f}")
print(f"n = {len(mm)} city-market cells. With n this small, report the direction,")
print("not the coefficient, and say so out loud.")

rule("DONE — every number above is reproducible from this file")
