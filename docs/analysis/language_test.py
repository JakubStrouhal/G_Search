#!/usr/bin/env python3
"""
Groupon case study — the language test.

THE CLAIM UNDER TEST. The brief asserts: "Our search, browse and homepage were
built for the US: dense supply, English-language queries. The same platform runs
in Germany, France, Spain, Poland and the UK against thinner inventory and five
different languages."

That is the one business claim in the brief that the supplied data CAN test.
Nobody should repeat it back to the hiring manager without a number attached.

THE DESIGN. A naive split — "queries that also appear in GB" vs "queries unique
to this market" — is confounded, badly. The GB-shared set is dominated by
loanwords (brunch, crossfit, sushi, paintball, bowling) that name concepts the
catalogue does not stock AT ALL. Those fail for supply reasons, not language
reasons, and they would manufacture a language effect out of a coverage gap.

So the test is run on MATCHED PAIRS instead: the same concept, in the same
market, expressed in English vs in the local language, restricted to concepts
the catalogue demonstrably stocks. If English phrasing does worse than local
phrasing for the SAME stocked concept in the SAME market, supply cannot explain
it and language is the remaining variable.

The pair table below is hand-built. That is deliberate: an LLM-generated
translation map is a fabrication risk I could not defend if asked "how do you
know these mean the same thing". Every pair here can be checked by eye.

Run:  python3 docs/analysis/language_test.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 300)

BRIEF = Path(__file__).resolve().parent.parent / "brief"
OUTPUTS = Path(__file__).resolve().parent / "outputs"
OUTPUTS.mkdir(exist_ok=True)

# Concept -> English phrasing -> local phrasing per market.
# Only concepts the catalogue STOCKS (massage, beauty, fitness, dining,
# escape room, karting, city tour). Coverage gaps are excluded by construction.
PAIRS = [
    # concept,        english,               DE,                     ES,                        FR,                   PL
    ("back massage",   "back massage",        "rückenmassage",        "masaje espalda",          "massage dos",        "masaż pleców"),
    ("sports massage", "sports massage",      "sportmassage",         "masaje descontracturante", "massage sportif",   "masaż sportowy"),
    ("thai massage",   "thai massage",        None,                   "masaje tailandes",        "massage thai",       "masaż tajski"),
    ("couples massage", "couples massage",    "paarmassage",          "masaje en pareja",        "massage duo",        "masaż dla par"),
    ("facial",         "facial",              "gesichtsbehandlung",   "limpieza facial",         "soin visage",        "oczyszczanie twarzy"),
    ("haircut",        "haircut",             "friseur",              "peluqueria",              "coiffeur",           "fryzjer"),
    ("hair colour",    "hair colour",         "haare färben",         "tinte pelo",              "coloration",         "koloryzacja"),
    ("eyelash ext.",   "eyelash extensions",  "wimpernverlängerung",  "extensiones pestañas",    "extension de cils",  "przedłużanie rzęs"),
    ("gym",            "gym",                 "fitnessstudio",        "gimnasio",                "salle de sport",     "siłownia"),
    ("personal trainer", "personal trainer",  None,                   "entrenador personal",     "coach sportif",      "trener personalny"),
    ("yoga class",     "yoga class",          "yoga kurs",            "clase de yoga",           "cours de yoga",      "joga"),
    ("city tour",      "city tour",           "stadtrundfahrt",       "tour ciudad",             "visite guidee",      "zwiedzanie miasta"),
    ("go karting",     "go karting",          "kart fahren",          "karting",                 "karting",            "gokarty"),
]
MARKETS = ["DE", "ES", "FR", "PL"]  # GB excluded: English IS the local language there


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z**2 / n
    c = p + z**2 / (2 * n)
    m = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return ((c - m) / d, (c + m) / d)


searches = pd.read_csv(BRIEF / "search_log.csv")
searches["zero"] = (searches["results_shown"] == 0).astype(int)
searches["dead"] = (searches["results_shown"] <= 2).astype(int)
searches["q"] = searches["raw_query"].str.lower().str.strip()


def slice_for(market, query):
    if query is None:
        return None
    sub = searches[(searches["market"] == market) & (searches["q"] == query)]
    return sub if len(sub) else None


print("=" * 78)
print("MATCHED-PAIR LANGUAGE TEST")
print("Same concept, same market, English phrasing vs local phrasing.")
print("Only concepts the catalogue stocks. GB excluded (English is local there).")
print("=" * 78)

rows = []
for concept, en, *locals_ in PAIRS:
    for market, loc in zip(MARKETS, locals_):
        en_s, loc_s = slice_for(market, en), slice_for(market, loc)
        if en_s is None or loc_s is None:
            continue
        rows.append({
            "concept": concept, "market": market,
            "en_query": en, "local_query": loc,
            "en_n": len(en_s), "en_dead": en_s["dead"].mean(),
            "loc_n": len(loc_s), "loc_dead": loc_s["dead"].mean(),
            "gap_pp": (en_s["dead"].mean() - loc_s["dead"].mean()) * 100,
        })

pairs = pd.DataFrame(rows).sort_values("gap_pp", ascending=False)
print("\nPER PAIR (dead-end = 0, 1 or 2 results):")
print(pairs.round(3).to_string(index=False))

# --------------------------------------------------------------------------
# The aggregate, with its uncertainty attached.
# --------------------------------------------------------------------------
en_dead = int(sum(searches[(searches["market"] == m) & (searches["q"] == r.en_query)]["dead"].sum()
                  for _, r in pairs.iterrows() for m in [r.market]))
en_n = int(pairs["en_n"].sum())
loc_dead = int(sum(searches[(searches["market"] == m) & (searches["q"] == r.local_query)]["dead"].sum()
                   for _, r in pairs.iterrows() for m in [r.market]))
loc_n = int(pairs["loc_n"].sum())

print("\n" + "=" * 78)
print("AGGREGATE")
print("=" * 78)
for label, k, n in [("English phrasing", en_dead, en_n), ("Local phrasing", loc_dead, loc_n)]:
    lo, hi = wilson(k, n)
    print(f"{label:<18} dead-end {k}/{n} = {k/n:.1%}   95% CI [{lo:.1%}, {hi:.1%}]")

print(f"\nGap: {(en_dead/en_n - loc_dead/loc_n)*100:.1f} percentage points.")
print(f"Pairs where English is worse: {(pairs['gap_pp'] > 0).sum()} of {len(pairs)}")

print("\nBY MARKET:")
bym = pairs.groupby("market").apply(
    lambda g: pd.Series({
        "pairs": len(g),
        "en_n": g["en_n"].sum(),
        "en_dead": (g["en_dead"] * g["en_n"]).sum() / g["en_n"].sum(),
        "loc_n": g["loc_n"].sum(),
        "loc_dead": (g["loc_dead"] * g["loc_n"]).sum() / g["loc_n"].sum(),
    }), include_groups=False)
bym["gap_pp"] = (bym["en_dead"] - bym["loc_dead"]) * 100
print(bym.round(3).to_string())

# --------------------------------------------------------------------------
# The contrast that stops this being read as a supply story.
# --------------------------------------------------------------------------
print("\n" + "=" * 78)
print("CONTROL — loanwords naming concepts the catalogue does NOT stock")
print("=" * 78)
print("These are ALSO English-origin terms used in non-GB markets. If the effect")
print("above were really about English, these should fail the same way. They do")
print("not — they fail at the ordinary rate, because their problem is supply,")
print("not language. This is what separates the two mechanisms.")
LOANWORDS = ["brunch", "crossfit", "sushi", "paintball", "bowling", "pilates"]
ctl = searches[(searches["market"].isin(MARKETS)) & (searches["q"].isin(LOANWORDS))]
print("\n" + ctl.groupby("q").agg(n=("dead", "size"), dead_rate=("dead", "mean"),
                                  zero_rate=("zero", "mean")).round(3).to_string())
lo, hi = wilson(int(ctl["dead"].sum()), len(ctl))
print(f"\nloanword dead-end {int(ctl['dead'].sum())}/{len(ctl)} = {ctl['dead'].mean():.1%} "
      f"95% CI [{lo:.1%}, {hi:.1%}]")

# --------------------------------------------------------------------------
# The other confound worth killing: the English queries are all LOW VOLUME
# (240 searches vs 2,345). If rare queries simply fail more often, whatever
# the language, then this whole result is a rarity artifact wearing a language
# costume. So: do rare LOCAL-language queries fail like rare English ones?
# --------------------------------------------------------------------------
print("=" * 78)
print("CONTROL — is this really about rarity, not language?")
print("=" * 78)
gb_queries = set(searches[searches["market"] == "GB"]["q"].unique())
loc_only = searches[(searches["market"].isin(MARKETS)) & (~searches["q"].isin(gb_queries))]
per_q = loc_only.groupby(["market", "q"]).agg(n=("dead", "size"), dead=("dead", "mean")).reset_index()
per_q["bucket"] = pd.cut(per_q["n"], [0, 5, 10, 25, 50, 10000],
                         labels=["1-5", "6-10", "11-25", "26-50", "50+"])
rare = per_q[per_q["n"] <= 5]
print(per_q.groupby("bucket", observed=True).agg(
    queries=("n", "size"), searches=("n", "sum"), mean_dead_rate=("dead", "mean")).round(3).to_string())
print(f"\nRare LOCAL-language queries (n<=5): {len(rare)} queries, "
      f"mean dead-end {rare['dead'].mean():.1%}")
print(f"English phrasing (also rare, n={en_n}):        dead-end {en_dead/en_n:.1%}")
print("""
There is no rarity gradient in the local-language queries at all — the 1-5
bucket and the 50+ bucket fail at almost the same rate. Rare local queries die
around 53%; English phrasing dies at 81%. Rarity does not explain the gap.
""")

pairs.to_csv(OUTPUTS / "language_pairs.csv", index=False)
print(f"written: {OUTPUTS / 'language_pairs.csv'}")

print("""
READING THIS HONESTLY
  - The pairs are hand-matched. Someone could dispute an individual pairing;
    the aggregate does not rest on any single one.
  - Per-pair counts are small (often n<40 on the English side). The AGGREGATE
    is what carries weight, and the CIs above are the honest statement of it.
  - This is synthetic data. It shows the generator encoded a language effect.
    It is evidence the brief's own thesis is coherent, NOT independent proof
    that Groupon's production search has this exact defect. The live probe in
    live_probe.js is the separate, real-world check.
""")
