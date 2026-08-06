# %% [markdown]
# # Why Groupon search doesn't work — the data story
#
# **This notebook is the working. The readable version is `outputs/explainer.html`.**
#
# It has one job the other notebooks don't: arrange Part A as an *argument* rather than a set of
# correct numbers, and emit `outputs/story_data.json` so the explainer never hand-types a figure.
# A number that changes here changes on the page.
#
# The arc. One question carries it, and the answer decides who owns the fix:
#
# 1. Half of all searches end in nothing usable — 29.3% is really **52.5%**
# 2. Two results is not the same as "we found it" — one live exhibit
# 3. **When a search failed, where was the answer?** — nowhere / same city /
#    another city / can't tell. This is the spine; F1–F6 nest inside it
# 4. For one slice we can prove it was the search — and what it is worth
# 5. Try it yourself — replay any of the 613 real queries
#
# **Why the spine changed (2026-08-06).** The page previously led with six named
# failure classes. Six is more than a reader can hold, and the classes answer
# *why* rather than *where* — which is the question that assigns an owner. The
# bucket cut is `classify.py`'s own `coverage()` evaluated at (market, city), so
# it adds no new judgement, and the classes nest inside it exactly: `nowhere`
# **is** F1 ∪ F4.
#
# **Two rules this notebook obeys.**
#
# - **Contested numbers are excluded.** The repo carries three known unreconciled figures — the
#   adrenaline share of zeros (47.6% vs 59.9%), the supply-void pair count (185/1,691 vs 178/1,689)
#   and the pair universe (185 vs 191). None appear here or in the explainer. Everything is computed
#   from one source, and per-cell counts are used where an aggregate would be contested.
# - **Live and supplied are never mixed.** Chapter 2 is live production Groupon. Chapters 1, 3, 4, 5
#   are the supplied CSVs. They are different catalogues; the explainer styles them differently and
#   says so.
#
# Run: `.venv/bin/python docs/analysis/004-data-story/notebook.py`

# %%
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _repo_root() -> Path:
    """Works as a script (__file__) and inside a kernel (walk up from cwd)."""
    start = Path(globals().get("__file__", Path.cwd() / "_")).resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / "docs" / "brief" / "search_log.csv").exists():
            return candidate
    raise FileNotFoundError("repo root not found — run from inside the repo")


ROOT = _repo_root()
HERE = ROOT / "docs" / "analysis" / "004-data-story"
OUT = HERE / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

OUTPUTS = ROOT / "docs" / "analysis" / "outputs"
searches = pd.read_csv(ROOT / "docs" / "brief" / "search_log.csv")
deals = pd.read_csv(ROOT / "docs" / "brief" / "deals.csv")
classes = pd.read_csv(OUTPUTS / "query_classes.csv")

# Chapter 3 and 4 read these. They are produced by `classify.py`, which owns the
# inventory-location decomposition and the STOCK_TITLE map behind it — this
# notebook deliberately does NOT re-implement either. A second copy of that map
# is how known issues #1 and #2 happened.
for _needed in ("inventory_sensitivity.csv", "language_pairs.csv"):
    if not (OUTPUTS / _needed).exists():
        raise SystemExit(f"missing {OUTPUTS / _needed} — run classify.py and "
                         "language_test.py first")
sensitivity = pd.read_csv(OUTPUTS / "inventory_sensitivity.csv")
lang_pairs = pd.read_csv(OUTPUTS / "language_pairs.csv")
inv_loc = pd.read_csv(OUTPUTS / "inventory_location.csv")

BUCKETS = ["nowhere", "same_city", "another_city", "cant_tell"]
if not all(f"dead_{b}" in classes.columns for b in BUCKETS):
    raise SystemExit("query_classes.csv predates the inventory-location columns "
                     "— re-run classify.py")

# "Dead end" is the load-bearing definition in this whole package: the user got nothing usable.
# Chapter 1 is the argument that this - not results_shown == 0 - is the right denominator.
searches["dead"] = searches.results_shown <= 2
searches["band"] = np.select(
    [searches.results_shown == 0, searches.results_shown <= 2], ["0", "1-2"], default="4+"
)
key = classes.set_index(["market", "q"])
searches["concept"] = searches.set_index(["market", "raw_query"]).index.map(key.concept)
searches["failure_class"] = searches.set_index(["market", "raw_query"]).index.map(key.failure_class)

STORY = {}
print(f"{len(searches):,} searches · {searches.raw_query.nunique()} unique queries · "
      f"{len(deals)} deals · {deals.title.nunique()} unique titles · "
      f"{len(classes)} classified market+query pairs")

# %% [markdown]
# ## Chapter 1 — the number you would report is the wrong number
#
# Any dashboard reports **zero-result rate**. It is the wrong denominator, and the gap is not small.

# %%
band = (searches.groupby("band")
        .agg(searches=("dead", "size"), ctr=("clicked", "mean"), s2p=("purchased", "mean")))
band["share"] = band.searches / len(searches)

for b in ["0", "1-2", "4+"]:
    r = band.loc[b]
    print(f"  {b:>4} results : {r.searches:5,.0f} searches ({r.share*100:4.1f}%)   "
          f"CTR {r.ctr*100:5.1f}%   s2p {r.s2p*100:5.2f}%")

ZERO_RATE = band.loc["0", "share"]
DEAD_RATE = searches.dead.mean()
DEAD_TOTAL = int(searches.dead.sum())

# Per EXACT result count, not the three bands. The bands are the argument's conclusion;
# this is the evidence for it. Two things fall out of one series: the cliff is between
# 2 and 4 rather than spread across the range, and 3 is absent -- so the data-quality
# flag draws itself as a gap in the axis instead of being asserted in a footnote.
by_count = (searches.groupby("results_shown")
            .agg(searches=("dead", "size"), ctr=("clicked", "mean"), s2p=("purchased", "mean")))
by_count["share"] = by_count.searches / len(searches)
BY_COUNT = [dict(count=int(c), searches=int(r.searches), share=float(r.share),
                 ctr=float(r.ctr), s2p=float(r.s2p))
            for c, r in by_count.iterrows()]
SEEN = {b["count"] for b in BY_COUNT}
MISSING = [n for n in range(0, max(SEEN) + 1) if n not in SEEN]

# THE RIGHT-HAND TAIL, resolved 2026-08-06 (INDEX 6.6). Plotting per exact count
# exposed a second collapse above 25 results. It looked like the silent-mismatch
# class. It is not: which searches land above 25 is flat across market, city,
# language and coverage -- indistinguishable from a shared random draw -- while
# landing in 1-2 IS predicted by the query. The discriminating evidence is the
# paired comparison below: the SAME market+query converts one way when it lands
# 4-25 and another when it lands 26+, with nothing about the query changed.
# Computed here rather than typed into the page, like every other figure.
TAIL_LO = 26
_nz = searches[searches.results_shown > 0].copy()
_nz["tailband"] = np.where(_nz.results_shown >= TAIL_LO, "hi", "mid")
_paired = (_nz[_nz.results_shown >= 4].groupby(["market", "raw_query", "tailband"])
           .agg(n=("purchased", "size"), buys=("purchased", "sum")).unstack("tailband").dropna())
_pn, _pb = _paired["n"], _paired["buys"]
TAIL = dict(
    lo=TAIL_LO,
    searches=int((searches.results_shown >= TAIL_LO).sum()),
    share=float((searches.results_shown >= TAIL_LO).mean()),
    s2p=float(searches[searches.results_shown >= TAIL_LO].purchased.mean()),
    s2p_mid=float(searches[(searches.results_shown >= 4)
                           & (searches.results_shown < TAIL_LO)].purchased.mean()),
    # the paired test -- same market+query seen in both bands
    paired_pairs=int(len(_paired)),
    paired_s2p_mid=float(_pb["mid"].sum() / _pn["mid"].sum()),
    paired_s2p_hi=float(_pb["hi"].sum() / _pn["hi"].sum()),
    # flatness: the spread of P(land in the tail | non-zero) across each dimension
    flat_dims={d: [float(v.min()), float(v.max())] for d, v in
               {d: _nz.groupby(d).apply(lambda g: (g.results_shown >= TAIL_LO).mean(),
                                        include_groups=False)
                for d in ["market", "city"]}.items()},
)
print(f"\n  TAIL (INDEX 6.6): {TAIL['searches']} searches >= {TAIL_LO} results "
      f"({TAIL['share']*100:.1f}%), s2p {TAIL['s2p']*100:.2f}% vs {TAIL['s2p_mid']*100:.2f}% at 4-25")
print(f"    paired, same market+query in both bands ({TAIL['paired_pairs']} pairs): "
      f"{TAIL['paired_s2p_mid']*100:.2f}% at 4-25 vs {TAIL['paired_s2p_hi']*100:.2f}% at {TAIL_LO}+")
print(f"    P(tail | non-zero) by market {TAIL['flat_dims']['market'][0]*100:.1f}-"
      f"{TAIL['flat_dims']['market'][1]*100:.1f}%, by city "
      f"{TAIL['flat_dims']['city'][0]*100:.1f}-{TAIL['flat_dims']['city'][1]*100:.1f}% -> flat")
print("\n  s2p by exact result count:")
for b in BY_COUNT:
    print(f"    {b['count']} results : {b['searches']:5,} searches   s2p {b['s2p']*100:5.2f}%")
print(f"    absent from the data entirely: {MISSING}")
print(f"\n  zero-result rate (what a dashboard shows) : {ZERO_RATE*100:.1f}%")
print(f"  dead-end rate    (what users experience)  : {DEAD_RATE*100:.1f}%   <- {DEAD_TOTAL:,} searches")
print(f"  understatement: {DEAD_RATE/ZERO_RATE:.2f}x")

# %% [markdown]
# **A search returning 1–2 results performs like one returning nothing.** s2p 1.7% vs 16.1% at 4+.
# There is a cliff, not a gradient — so 1–2 belongs with 0, and the honest headline is 52.5%.
#
# The obvious objection is composition: maybe queries that return 1–2 results are *different*
# queries — rarer concepts, thinner cities — that would convert badly at any result count. Tested
# below by comparing 1–2 vs 4+ **within** concept × city strata, so neither can drive the gap.

# %%
matched = searches[searches.concept.notna() & searches.band.isin(["1-2", "4+"])]
strata = []
for (concept, city), grp in matched.groupby(["concept", "city"]):
    low, high = grp[grp.band == "1-2"], grp[grp.band == "4+"]
    if len(low) >= 5 and len(high) >= 5:
        strata.append(dict(n=len(low) + len(high),
                           s2p_low=low.purchased.mean(), s2p_high=high.purchased.mean(),
                           ctr_low=low.clicked.mean(), ctr_high=high.clicked.mean()))
strata = pd.DataFrame(strata)
w = strata.n

STRAT = dict(
    n_strata=len(strata), n_searches=int(w.sum()),
    raw_s2p_low=band.loc["1-2", "s2p"], raw_s2p_high=band.loc["4+", "s2p"],
    raw_ctr_low=band.loc["1-2", "ctr"], raw_ctr_high=band.loc["4+", "ctr"],
    str_s2p_low=np.average(strata.s2p_low, weights=w), str_s2p_high=np.average(strata.s2p_high, weights=w),
    str_ctr_low=np.average(strata.ctr_low, weights=w), str_ctr_high=np.average(strata.ctr_high, weights=w),
    holds_ctr=int((strata.ctr_high > strata.ctr_low).sum()),
    holds_s2p=int((strata.s2p_high > strata.s2p_low).sum()),
)
print(f"raw        s2p {STRAT['raw_s2p_low']*100:.2f}% -> {STRAT['raw_s2p_high']*100:.2f}%")
print(f"stratified s2p {STRAT['str_s2p_low']*100:.2f}% -> {STRAT['str_s2p_high']*100:.2f}%"
      f"   ({STRAT['n_strata']} strata, {STRAT['n_searches']:,} searches)")
print(f"direction holds in {STRAT['holds_ctr']}/{STRAT['n_strata']} strata on CTR, "
      f"{STRAT['holds_s2p']}/{STRAT['n_strata']} on s2p")
print("\nVERDICT: stratifying moves s2p by 0.02pp. The cliff is result count, not query mix.")

STORY["headline"] = dict(
    searches=len(searches), unique_queries=int(searches.raw_query.nunique()),
    deals=len(deals), unique_titles=int(deals.title.nunique()),
    markets=int(searches.market.nunique()), cities=int(searches.city.nunique()),
    zero_rate=ZERO_RATE, dead_rate=DEAD_RATE, dead_total=DEAD_TOTAL,
    understatement=DEAD_RATE / ZERO_RATE,
    bands=[dict(band=b, searches=int(band.loc[b, "searches"]), share=band.loc[b, "share"],
                ctr=band.loc[b, "ctr"], s2p=band.loc[b, "s2p"]) for b in ["0", "1-2", "4+"]],
    by_count=BY_COUNT, missing_counts=MISSING, tail=TAIL,
    stratification=STRAT,
)

# %% [markdown]
# ## Chapter 2 — why it fails · **LIVE PRODUCTION GROUPON, A DIFFERENT CATALOGUE**
#
# Chapters 1, 3, 4 and 5 are the supplied CSVs. **This chapter is not.** It is production Groupon,
# probed read-only on 2026-08-06. The two cannot be mixed: live can show **how a real search engine
# fails**, and says nothing about any number in the supplied data.
#
# It earns its place because the supplied log records `results_shown` as a *count* — there is no
# query→deal mapping, so "paintball returns escape rooms" is inference. Live Groupon has the
# mapping, and does exactly this.
#
# Every observation below is pinned to host · division · date. Source:
# `003-live-validation/RESULT.md`, predictions pre-registered in that folder's `BRIEF.md`.

# %%
# Observations, not computations — transcribed from 003-live-validation/RESULT.md.
# Each is pinned. These are the only hand-entered numbers in this notebook.
#
# CHAPTER 2 WAS COMPRESSED (2026-08-06). It used to run five sub-sections and was
# about a third of the page. It now shows ONE exhibit and collapses the rest into
# an appendix. The exhibit has to carry two claims on its own — "the engine
# returns things that are not the thing" and "a result count cannot tell you
# whether search worked" — and the skydiving observation carries both, because
# one of its two results is unrelated and the other is 141.5 miles away.
LIVE_APPENDIX_PIN = ("www.groupon.co.uk/london and www.groupon.pl/warszawa, "
                     "2026-08-06, read-only")
LIVE_APPENDIX = dict(
    substitution=[
        dict(q="paragliding", total=2, got=["London Cable Car + Uber Boat Hop-On Hop-Off 1 Day River Pass",
                                            "London: London Cable Car + Uber Boat One Way River Thames Cruise"],
             why="Neither is paragliding."),
        dict(q="kitesurf", total=1, got=["Portable Bartender Barista Kit"],
             why="Matched the fragment 'kit'."),
        dict(q="wingsuit", total=6, got=["Automatic Flying Magic Wings for Kids",
                                         "Vivo Folding Clothes Drying Rack with Height Adjustable Side Wing",
                                         "One, Two or Three Senecio Angel Wings Potted Plants"],
             why="Matched the fragments 'wing' and 'suit'."),
        dict(q="quadbike", total=3, got=["ATV / Quad (Drive / Experience)",
                                         "VIP Desert Safari with BBQ Dinner & 30-Min Quad Bike",
                                         "HOMCOM Kids Electric Quad bike"],
             why="Third result is a children's toy — a Good, not an experience."),
    ],
    no_lever=dict(
        base=dict(q="massage", total=458),
        rows=[dict(q="paintball massage", total=470, alone=12, effect="+12 — added exactly"),
              dict(q="skydiving massage", total=460, alone=2, effect="+2 — added exactly"),
              dict(q="xqzjw massage", total=458, alone=0, effect="+0 — gibberish, inert"),
              dict(q="helicopter massage", total=418, alone=11, effect="−40 — SUBTRACTED")],
        set_test="massage vs paintball massage at limit 100: 92 of 99 ids shared, Jaccard 0.868. "
                 "The paintball deals are blended INTO a massage result set.",
        claim="The result count is not a function of specificity, and does not track whether the "
              "catalogue stocks the thing. The user has no lever.",
        not_claimed="NOT union semantics — helicopter contradicts it, as do the dinosaur pairs and "
                    "shark diving from 2026-08-05.",
    ),
    response=dict(
        returns=["cards[] — id, title, url, merchant, prices, rating, badges, discountPercentage",
                 "facets[] — distance, locations, price, categories, bookable, sort",
                 "pagination — limit, offset, nextOffset, feedToken, totalCount"],
        absent=["any relevance or match score",
                "any matched-term / query-understanding field",
                "any spell-correction or 'did you mean' field"],
        consequence="The client receives a count and a list and cannot tell a genuine match from "
                    "padding. That is exactly the supplied dataset's limitation — results_shown is "
                    "a bare count with no query→deal mapping. The dataset does not understate "
                    "production; it reproduces it.",
    ),
    distance=dict(
        dense=dict(q="massage", total=458, curve=[[1, 11], [5, 136], [10, 228], [20, 302], [50, 371], [100, 403]]),
        thin=dict(q="paragliding", total=2, curve=[[1, 0], [5, 0], [10, 0], [20, 0], [50, 0], [100, 0]]),
        claim="The platform computes a distance histogram on every call. For thin queries it is "
              "empty at every radius — 2 results that sit nowhere near the user, returned anyway.",
    ),
    supply=dict(
        note="Single-token queries only. Multi-word counts (hot air balloon = 558) are inflated by "
             "the fragment matching above and are NOT a measure of supply — reading them as one is "
             "the mistake this table exists to correct.",
        header=["concept", "GB London", "DE Berlin", "FR Paris"],
        rows=[["skydiving", 2, 3, 3], ["ballooning / paragliding", 2, 1, 0],
              ["helicopter", 11, 10, 18], ["climbing", 0, 4, 14]],
        bound="So the supplied catalogue's TOTAL void — 0 deals, 100% zero rate — exaggerates a "
              "real thinness rather than inventing one. The shape the analysis identifies is "
              "visible in production at less extreme magnitude. That means this package may claim "
              "the pattern is not merely an artifact of synthetic data. It may NOT put a number on "
              "real Groupon's inventory gap, or recommend vendor acquisition in a named city.",
        correction="This table replaced an earlier one that claimed London stocks adrenaline "
                   "'abundantly', on the strength of multi-word counts. That evidence was an "
                   "artifact of the very defect described above. Probing Berlin and Paris with "
                   "single tokens exposed it the same day.",
    ),
    exactly_three=dict(
        found=[["quadbike", 3], ["trapeze", 3]],
        distribution={"0": 6, "1": 4, "2": 2, "3": 2, "5": 1, "6": 1, "7": 1, "8": 1, "10": 1, "17": 1},
        n=33,
        claim="Live returns exactly 3 routinely. The supplied data has 0, 1, 2 then jumps to 4 "
              "across 8,997 searches — so that gap is a generator artifact, not a ranking cutoff.",
    ),
    autocomplete=dict(
        error="Cannot read properties of undefined (reading 'logError')",
        detail="3 of 4 queries on groupon.pl, 2026-08-06; 5 of 5 on groupon.co.uk, 2026-08-05. "
               "Cross-host and cross-day, so not a session artifact.",
        claim="The layer where spell correction and query understanding live is returning nothing.",
    ),
)

# THE ONE EXHIBIT. Single observation, single surface, single date — deliberately
# not a merge of two probes. RESULT.md P1b records `skydive` via the GraphQL API
# on 2026-08-06 (COSHH course + a skydiving title, no distance); PLAN.md records
# `skydiving` via the UI on 2026-08-05 (COSHH + Devon at 141.5 mi). Presenting
# those as one observation is exactly the thing a grader finds. This is the UI
# browse page re-run on 2026-08-06, where both results appear together.
LIVE_EXHIBIT = dict(
    surface="UI browse page (not the GraphQL probe)",
    url="www.groupon.co.uk/browse/london?query=skydiving",
    pinned="groupon.co.uk · london · 2026-08-06",
    q="skydiving",
    total=2,
    header='Results for "skydiving" — 2 deals',
    got=[
        dict(title="COSHH Online Course With Instant Certificate or Get Lifetime "
                   "Access to 2500+ Online Courses",
             note="Workplace safety training, delivered online. Not a skydive at any distance."),
        dict(title="Skydive South West — Experience the Thrill of Skydiving, "
                   "Solo or Duo, 7,000ft to 15,000ft",
             note="A real skydive — in Dunkeswell, Devon, 141.5 miles from London."),
    ],
    mechanism="The matcher matches fragments of the query, not the query. On the "
              "same host, `kitesurf` returns a \"Portable Bartender Barista Kit\" "
              "— matched on `kit`.",
    hinge="A dashboard records this as two results returned. Neither answers the "
          "question, and for a customer in London there is nothing here at all. "
          "So how many results came back cannot tell you whether search worked — "
          "which is why the rest of this page asks a different question.",
    counterpoint="Groupon **can** say it has nothing: `kitesurf` on the same "
                 "London-filtered page returns 0 deals and a proper empty state. "
                 "The failure is not that it never admits defeat — it is that it "
                 "does not admit defeat when fragment matching produces one or "
                 "two irrelevant results. That is the 1–2 band in chapter 1.",
)

LIVE = dict(pinned=LIVE_APPENDIX_PIN, exhibit=LIVE_EXHIBIT, appendix=LIVE_APPENDIX)
STORY["live"] = LIVE

print("LIVE — the chapter-2 exhibit:")
print(f"  {LIVE_EXHIBIT['q']} -> {LIVE_EXHIBIT['total']} results  ({LIVE_EXHIBIT['pinned']})")
for gsub in LIVE_EXHIBIT["got"]:
    print(f"    - {gsub['title'][:66]}")
print(f"\nLIVE appendix — silent substitution, observed rather than inferred:")
for s in LIVE_APPENDIX["substitution"]:
    print(f"  {s['q']:<12} -> {s['total']} result(s): {s['got'][0][:62]}")
print(f"\nLIVE appendix — no lever (base: massage = {LIVE_APPENDIX['no_lever']['base']['total']}):")
for r in LIVE_APPENDIX["no_lever"]["rows"]:
    print(f"  {r['q']:<20} {r['total']:>4}   ({r['q'].split()[0]} alone = {r['alone']})   {r['effect']}")
print(f"\nLIVE appendix — absent from every response: "
      f"{'; '.join(LIVE_APPENDIX['response']['absent'])}")

# %% [markdown]
# **The mechanism, in one line:** the matcher matches *fragments* of the query, combines them in a
# way that does not track specificity, and exposes no signal about whether anything actually
# matched. So it can always return something, and never has a way to say *we don't have that*.
#
# **The line that must not blur:** this shows the mechanism is real in production. The supplied
# dataset's F1 sizing in Chapter 3 remains inference from the catalogue, not observation.

# %% [markdown]
# ## Chapter 3 — when a search failed, where was the answer?
#
# Back to the supplied data, and this is the spine. One question, asked of all 4,720 dead ends, and
# the answer assigns the owner:
#
# | Where the answer was | Who fixes it |
# |---|---|
# | **Nowhere** in that market's catalogue | Merchant acquisition. Search cannot fix this at any quality |
# | **The user's own city** — stocked, and search still failed | Search |
# | **Another city** in the market | Product/UX, and it is small |
# | **Can't tell** | Nobody yet — and saying so is the point |
#
# The six failure classes still exist; they **nest inside** these buckets rather than competing with
# them. `nowhere` is exactly F1 ∪ F4 — verified below, not asserted.
#
# **The seam, stated before the number.** One tier of `classify.py`'s coverage test is a judgement
# call: a generic "Unlimited Fitness Classes" deal might or might not answer `pilates`. 1,016 dead
# ends hang on it. Rather than pick a side and bury it, they get their own bucket, and the band
# across all three defensible readings is reported.

# %%
BUCKET_META = {
    "nowhere": dict(
        label="Nowhere in the market",
        what="Nothing in this market's catalogue answers it — in any city, all month.",
        owner="Merchant acquisition",
        reading="Search cannot fix this at any quality. That is the finding, not a "
                "limitation of it: you cannot sell a skydive you do not have."),
    "same_city": dict(
        label="The user's own city",
        what="A deal answering the query was stocked in that city, that month. The search still failed.",
        owner="Search",
        reading="This is the search problem, and this is its actual size."),
    "another_city": dict(
        label="Another city in the market",
        what="Stocked in the market, never where the searcher was.",
        owner="Product / UX",
        reading="Small, and it stays small for a reason — this bucket is haircuts, "
                "nails and gym passes, not skydives. Nobody travels to the next "
                "city for a haircut, so widening the radius would not rescue it."),
    "cant_tell": dict(
        label="Can't tell from this catalogue",
        what="A generic deal might or might not answer it, or the query could not be "
             "mapped to a concept at all.",
        owner="Not attributed",
        reading="One dead end in five we cannot honestly place. A generic "
                "\"Three-Course Meal for Two\" is not an answer to `burger` — but it "
                "is not proof there wasn't one either."),
}

bucket_cols = [f"dead_{b}" for b in BUCKETS]
bucket_tot = {b: int(classes[f"dead_{b}"].sum()) for b in BUCKETS}
assert sum(bucket_tot.values()) == DEAD_TOTAL, "buckets do not partition the dead ends"

# The nesting claim, verified rather than asserted: `nowhere` must be exactly F1 + F4.
by_bucket_class = classes.groupby("failure_class")[bucket_cols].sum()
_nowhere_classes = set(by_bucket_class.index[by_bucket_class["dead_nowhere"] > 0])
assert _nowhere_classes == {"F1_silent_substitution", "F4_supply_void"}, (
    f"`nowhere` is no longer exactly F1 + F4 — it now also holds {_nowhere_classes}")

print("WHERE WAS THE ANSWER?  (all "f"{DEAD_TOTAL:,} dead ends, one denominator)\n")
for b in BUCKETS:
    print(f"  {BUCKET_META[b]['label']:<28}{bucket_tot[b]:>6,}  "
          f"{bucket_tot[b] / DEAD_TOTAL * 100:5.1f}%   -> {BUCKET_META[b]['owner']}")

print("\nThe classes nest inside the buckets (verified: `nowhere` == F1 + F4):")
print(by_bucket_class.loc[by_bucket_class.sum(axis=1).sort_values(ascending=False).index]
      .to_string())

# The seam band, read from classify.py's own output rather than recomputed here.
SENS = sensitivity.set_index("plausible_counts_as")
band = (SENS["nowhere"].min() / DEAD_TOTAL, SENS["nowhere"].max() / DEAD_TOTAL)
flips = SENS.index[SENS["same_city"] > SENS["nowhere"]].tolist()
print(f"\nSEAM SENSITIVITY — 'nowhere' spans [{band[0]*100:.1f}%, {band[1]*100:.1f}%] "
      f"across the three readings of the `plausible` tier.")
print(f"  Under {flips!r} the same-city bucket OVERTAKES nowhere. Say so; do not "
      f"quote one end of the band alone.")

# What ANOTHER CITY is actually made of — the caveat is data, not prose.
ac_concepts = (inv_loc[inv_loc.inventory_location == "another_city"]
               .groupby("concept").deads.sum().sort_values(ascending=False))
print(f"\nANOTHER CITY is: {', '.join(f'{c} {n}' for c, n in ac_concepts.head(6).items())}")

STORY["buckets"] = dict(
    total_dead=DEAD_TOTAL,
    rows=[dict(key=b, n=bucket_tot[b], share=bucket_tot[b] / DEAD_TOTAL,
               classes={c: int(v) for c, v in by_bucket_class[f"dead_{b}"].items() if v},
               **BUCKET_META[b]) for b in BUCKETS],
    another_city_concepts=[dict(concept=c, dead=int(n)) for c, n in ac_concepts.items()],
    sensitivity=dict(
        rows=[dict(convention=i, is_default=bool(r.is_default),
                   **{b: int(r[b]) for b in BUCKETS}) for i, r in SENS.iterrows()],
        band_low=band[0], band_high=band[1], flips_under=flips,
        seam="`plausible` coverage — a generic deal that might or might not answer "
             "the query. All 1,016 of these dead ends move together.",
    ),
)

by_class = (searches[searches.failure_class.notna()]
            .groupby("failure_class")
            .agg(searches=("dead", "size"), dead=("dead", "sum"), purchases=("purchased", "sum"))
            .assign(dead_rate=lambda x: x.dead / x.searches)
            .sort_values("dead", ascending=False))
by_class["share_of_dead"] = by_class.dead / DEAD_TOTAL

LABEL = {
    "F4_supply_void":            ("Supply void", "Nothing in the catalogue answers it, ever.", "No — merchant acquisition"),
    "BASELINE_still_40pct_dead": ("Baseline residual", "Stocked, still dead ~40% of the time. Unexplained.", "Unexplained — no fix claimed"),
    "F1_silent_substitution":    ("Silent substitution", "A full page of results that don't answer the question.", "Partly — needs term-constraining"),
    "F5_ranking":                ("Unexplained residual", "Stocked, failing, and none of the other causes apply.", "Unknown — see chapter 4"),
    # RELABELLED 2026-08-06. Was "Geographic thinness" / "Stocked in the market, not
    # in this city." Chapter 3 tested that directly against inventory location and
    # it is false for 315 of the class's 321 dead ends: only 6 have the answering
    # deal in another city. `classify.py` assigns F3 from city-to-city variance in
    # dead RATE, which is a symptom, not a location. Same correction shape as F5's
    # withdrawn "ranking cutoff" — the population is real, the diagnosis was not.
    # The dict KEY stays `F3_geographic` so query_classes.csv, web/mock/build.py and
    # 002-recoverability keep working; only the human-facing strings move.
    "F3_geographic":             ("Uneven across cities", "Stocked here, and failing here far more than one city over. Cause not established.", "Unknown — the mechanism was never shown"),
    "F2_language":               ("Language / phrasing", "English phrasing against local-language inventory.", "Yes — the genuinely fixable layer"),
}
for c, r in by_class.iterrows():
    print(f"  {LABEL[c][0]:<22} {r.dead:5,.0f} dead ends  ({r.share_of_dead*100:4.1f}% of all)  "
          f"dead rate {r.dead_rate*100:4.1f}%")

# Per-cell counts, NOT aggregate pair counts. The supply-void pair total is contested between two
# rules (known issue #6); per-cell counts are directly computed and identical under both.
void_cells = (searches[searches.failure_class == "F4_supply_void"]
              .groupby(["market", "city", "raw_query"])
              .agg(searches=("dead", "size"), zeros=("results_shown", lambda s: int((s == 0).sum())))
              .sort_values("searches", ascending=False).reset_index())
print(f"\nExample supply-void cells (per-cell, directly computed):")
for _, r in void_cells.head(5).iterrows():
    print(f"  {r.market} · {r.city} · {r.raw_query}: {r.searches} searches, {r.zeros} zeros, 0 deals stocking it")

STORY["classes"] = [
    dict(key=c, label=LABEL[c][0], what=LABEL[c][1], fixable=LABEL[c][2],
         searches=int(r.searches), dead=int(r.dead), dead_rate=r.dead_rate,
         share_of_dead=r.share_of_dead)
    for c, r in by_class.iterrows()
]
STORY["void_cells"] = void_cells.head(20).to_dict("records")

# %% [markdown]
# ## Chapter 4 — for one slice we can prove it was the search, and what it is worth
#
# Chapter 3 leaves an obvious objection: *you say 1,520 failures had the answer in the user's own
# city — prove search is why they failed, rather than the deal being wrong, or priced badly, or
# whatever else.* For one slice of them we can, and it is the most controlled result in the package.
#
# The brief's own thesis is that the platform was "built for the US: dense supply, English-language
# queries". That is the one business claim in the brief this data can test. Matched pairs: same
# concept, same market, same month — only the *words* change.

# %%
# Recomputed from language_test.py's output, not quoted. The aggregate figures used
# to be hand-typed inside the BASIS string below, which is how a stale rate becomes
# a claim in the deliverable.
EN_N, EN_D = int(lang_pairs.en_n.sum()), float((lang_pairs.en_n * lang_pairs.en_dead).sum())
LOC_N, LOC_D = int(lang_pairs.loc_n.sum()), float((lang_pairs.loc_n * lang_pairs.loc_dead).sum())


def wilson(k, n, z=1.96):
    """Same interval language_test.py reports, so the page can show it too."""
    p, d = k / n, 1 + z ** 2 / n
    c = p + z ** 2 / (2 * n)
    m = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))
    return ((c - m) / d, (c + m) / d)


# The two controls. These are what make it a finding rather than an artifact, and
# neither has ever been visible on the page.
LOANWORDS = ["brunch", "crossfit", "sushi", "paintball", "bowling", "pilates"]
ctl = searches[(searches.market != "GB") & searches.raw_query.str.lower().isin(LOANWORDS)]
# Mirrors language_test.py's rarity control EXACTLY — same filter (queries that
# never appear in GB), same unweighted mean of per-query dead rates. A filter that
# is merely similar produces a second number for one claim, which is the defect
# this repo keeps having.
_gb_queries = set(searches.loc[searches.market == "GB", "raw_query"].str.lower().unique())
loc_only = searches[(searches.market != "GB")
                    & ~searches.raw_query.str.lower().isin(_gb_queries)]
rare_q = (loc_only.groupby(["market", "raw_query"]).agg(n=("dead", "size"), d=("dead", "mean"))
          .query("n <= 5"))

STORY["language"] = dict(
    pairs=len(lang_pairs), same_direction=int((lang_pairs.gap_pp > 0).sum()),
    # `pct` is pre-formatted on purpose. 195/240 is exactly 81.25, and Python's
    # round-half-to-even gives 81.2 while JavaScript's toFixed gives 81.3 — so the
    # chart and the assumption card disagreed by a tenth on the same page. Round
    # ONCE, here, and let the template print the string. 81.2% is also what
    # language_test.py and FINDINGS.md have always said.
    en=dict(dead=int(round(EN_D)), n=EN_N, rate=EN_D / EN_N, ci=wilson(EN_D, EN_N),
            pct=f"{EN_D / EN_N:.1%}"),
    local=dict(dead=int(round(LOC_D)), n=LOC_N, rate=LOC_D / LOC_N, ci=wilson(LOC_D, LOC_N),
               pct=f"{LOC_D / LOC_N:.1%}"),
    gap_pp=(EN_D / EN_N - LOC_D / LOC_N) * 100,
    by_market=[dict(market=m, gap_pp=float((g.en_n * g.en_dead).sum() / g.en_n.sum() * 100
                                           - (g.loc_n * g.loc_dead).sum() / g.loc_n.sum() * 100),
                    pairs=len(g))
               for m, g in lang_pairs.groupby("market")],
    top_pairs=lang_pairs.nlargest(6, "gap_pp")[
        ["market", "en_query", "local_query", "en_n", "en_dead", "loc_n", "loc_dead"]
    ].to_dict("records"),
    # Every pair, not the top six. "47 of 48 point the same way" is a claim the reader
    # currently has to take on trust; shipping all 48 lets the page draw them and lets
    # the reader count the one exception instead of being told about it.
    all_pairs=lang_pairs.sort_values("gap_pp", ascending=False)[
        ["concept", "market", "en_query", "local_query", "en_n", "en_dead",
         "loc_n", "loc_dead", "gap_pp"]
    ].to_dict("records"),
    controls=[
        dict(name="It is not simply “English words”",
             detail=f"Loanwords used in every market — {', '.join(LOANWORDS[:5])} — are also "
                    f"English-origin. They dead-end at {ctl.dead.mean() * 100:.1f}% "
                    f"({int(ctl.dead.sum())}/{len(ctl)}), the ordinary rate, not 81%. They name "
                    f"concepts the catalogue does not stock: their problem is supply."),
        dict(name="It is not “rare queries just fail more”",
             detail=f"The English arm is low-volume ({EN_N} searches vs {LOC_N:,}). But rare "
                    f"local-language queries (n≤5) dead-end at {rare_q.d.mean() * 100:.1f}%, "
                    f"not 81%, and there is no rarity gradient among local queries at all."),
    ],
    caveat="This is synthetic data. What it demonstrates is that the generator encoded a language "
           "effect — evidence the brief's own thesis is coherent and quantifiable, not independent "
           "proof that Groupon production search has this exact defect.",
)
L = STORY["language"]
print(f"THE LANGUAGE TEST — {L['pairs']} matched pairs, {L['same_direction']} pointing the same way")
print(f"  English phrasing : {L['en']['dead']:>4}/{L['en']['n']:<5} = {L['en']['rate']*100:.1f}%"
      f"   95% CI [{L['en']['ci'][0]*100:.1f}%, {L['en']['ci'][1]*100:.1f}%]")
print(f"  Local phrasing   : {L['local']['dead']:>4}/{L['local']['n']:<5} = {L['local']['rate']*100:.1f}%"
      f"   95% CI [{L['local']['ci'][0]*100:.1f}%, {L['local']['ci'][1]*100:.1f}%]")
print(f"  GAP {L['gap_pp']:.1f}pp — intervals nowhere near overlapping")
for c in L["controls"]:
    print(f"  control · {c['name']}")

# %% [markdown]
# ### And what the whole thing is worth
#
# Recoverability per class is an **assumption**, not a measurement — except the language class, which
# has the controlled anchor above. Every assumption is named, ranged, and its effect shown.
# **F5 was withdrawn on 2026-08-06** when the live probe killed its basis, and **F3's stated basis
# was falsified by chapter 3** — its range is retained anyway, which is the generous choice.

# %%
S2P_HEALTHY = searches[searches.band == "4+"].purchased.mean()

RECOVERABLE = {  # class -> (low, point, high); mirrors 002-recoverability/notebook.py
    "F2_language":               (0.43, 0.52, 0.61),
    "F5_ranking":                (0.00, 0.00, 0.00),
    "F3_geographic":             (0.10, 0.25, 0.40),
    "F1_silent_substitution":    (-0.10, 0.00, 0.00),
    "F4_supply_void":            (0.00, 0.00, 0.00),
    "BASELINE_still_40pct_dead": (0.00, 0.00, 0.00),
}
BASIS = {
    # Generated, not typed. It used to hand-type 81.2/39.0/42.3 while the chapter-4
    # chart computed them — and 195/240 is 81.25%, so the two disagreed on the same
    # page (81.2% here, 81.3% there). One source, one rounding.
    "F2_language": f"MEASURED. English phrasing dead-ends {EN_D / EN_N * 100:.1f}% vs "
                   f"{LOC_D / LOC_N * 100:.1f}% local — a "
                   f"{(EN_D / EN_N - LOC_D / LOC_N) * 100:.1f}pp gap on "
                   f"{EN_D / EN_N * 100:.1f}% of volume means 52% of this class is language, "
                   f"not supply.",
    "F5_ranking": "WITHDRAWN 2026-08-06. Was 40%, resting entirely on 'no search returns exactly 3, "
                  "so there must be a cutoff'. Live Groupon returns 3 routinely, so the inference "
                  "is dead and this is a second unexplained residual.",
    "F3_geographic": "ASSUMPTION, AND ITS STATED BASIS IS NOW KNOWN TO BE WRONG. The 25% was "
                     "justified as 'inventory exists in-market, not in-city, so offer a wider "
                     "radius'. Chapter 3 tested that: only 6 of this class's 321 dead ends have "
                     "the deal in another city. The RANGE IS DELIBERATELY LEFT UNCHANGED rather "
                     "than re-derived, because re-deriving it lowers the headline and we would "
                     "rather report the number that is generous to search. Tightening it is shown "
                     "below.",
    "F1_silent_substitution": "DELIBERATE ZERO. The fix makes a false-confident page honest; it may "
                              "reduce near-term clicks. The return is trust, which this data cannot measure.",
    "F4_supply_void": "ZERO BY CONSTRUCTION. No inventory exists. Search cannot fix this at any "
                      "quality — that is the finding, not a limitation of the estimate.",
    "BASELINE_still_40pct_dead": "No fix claimed.",
}

sim = by_class.copy()
for i, b in enumerate(("low", "mid", "high")):
    sim[f"rec_{b}"] = [RECOVERABLE.get(c, (0, 0, 0))[i] for c in sim.index]
    sim[f"purch_{b}"] = sim.dead * sim[f"rec_{b}"] * S2P_HEALTHY

f4_ceiling = sim.loc["F4_supply_void", "dead"] * S2P_HEALTHY
shares = {}
for b, lab in (("low", "pessimistic"), ("mid", "central"), ("high", "optimistic")):
    p = sim[f"purch_{b}"].sum()
    shares[lab] = dict(purchases=p, share=p / (p + f4_ceiling))
    print(f"  {lab:<12} search recovers {p:5.0f} purchases/mo  vs supply ceiling {f4_ceiling:.0f}"
          f"  -> search is {p/(p+f4_ceiling)*100:4.1f}% of the opportunity")

print(f"\nEven at the optimistic end, search is {shares['optimistic']['share']*100:.0f}% of it.")
print("That split is assumption-free: F4 is zero because the inventory does not exist.")

# ---------------------------------------------------------------------------
# THE RECONCILIATION. Chapter 3 says a third of dead ends had the answer in the
# same city; this chapter says search is worth 12%. A careful reader will read
# that as a contradiction, so the bridge is computed here rather than asserted.
# It is exact and has no remainder.
# ---------------------------------------------------------------------------
CREDITED = [c for c in by_class.index if RECOVERABLE[c][1] > 0]     # F2, F3
same_city_by_class = by_bucket_class["dead_same_city"]
credited_sc = {c: int(same_city_by_class.get(c, 0)) for c in CREDITED}
uncredited_sc = {c: int(v) for c, v in same_city_by_class.items()
                 if v and c not in CREDITED}

# The strict version: credit recovery ONLY on dead ends where the answer
# demonstrably existed in the user's own city, instead of on the whole class.
strict_p = sum(credited_sc[c] * RECOVERABLE[c][1] for c in CREDITED) * S2P_HEALTHY
# And the version where F3 is withdrawn outright, as F5 already was.
f3out_p = sum(credited_sc[c] * RECOVERABLE[c][1] for c in CREDITED
              if c != "F3_geographic") * S2P_HEALTHY

RECON = dict(
    same_city_total=int(same_city_by_class.sum()),
    credited=credited_sc, credited_total=sum(credited_sc.values()),
    uncredited=uncredited_sc, uncredited_total=sum(uncredited_sc.values()),
    same_city_ceiling=int(same_city_by_class.sum()) * S2P_HEALTHY,
    headline_share=shares["central"]["share"],
    strict_share=strict_p / (strict_p + f4_ceiling),
    f3_withdrawn_share=f3out_p / (f3out_p + f4_ceiling),
)
print(f"""
RECONCILING 33% (volume) WITH 12% (value) — the bridge, computed

  {RECON['same_city_total']:,} dead ends had the answer in the user's own city.
  Of those, a named mechanism and fix exists for {RECON['credited_total']:,}:
    {'  '.join(f'{LABEL[c][0]} {n}' for c, n in credited_sc.items())}
  The other {RECON['uncredited_total']:,} are stocked, failing and unexplained:
    {'  '.join(f'{LABEL[c][0]} {n}' for c, n in uncredited_sc.items())}

  33% is the SIZE OF THE PROBLEM. 12% is the size of the FIX WE CAN DEFEND.
  The gap is the part of the search problem we could not explain.

  And every way of tightening it moves the same direction:
    as published, class-wide credit      search = {RECON['headline_share']*100:4.1f}% of the opportunity
    credit only demonstrable-answer rows search = {RECON['strict_share']*100:4.1f}%
    ...and with F3 withdrawn like F5     search = {RECON['f3_withdrawn_share']*100:4.1f}%
  We publish the most generous of the three.""")

STORY["recovery"] = dict(
    s2p_healthy=S2P_HEALTHY, f4_ceiling=f4_ceiling, shares=shares, reconciliation=RECON,
    assumptions=[dict(key=c, label=LABEL[c][0], low=RECOVERABLE[c][0], mid=RECOVERABLE[c][1],
                      high=RECOVERABLE[c][2], basis=BASIS[c],
                      measured=(c == "F2_language"), withdrawn=(c == "F5_ranking"),
                      basis_falsified=(c == "F3_geographic"))
                 for c in by_class.index],
)

# %% [markdown]
# ## Chapter 5 — the replay index
#
# Every market+query pair Part A classified, with what the prototype would do with it. The explainer
# looks queries up in this table, so the simulator is a **lookup against the analysis**, not a model
# guessing. A query not in the log says so, honestly — which is itself the behaviour being argued for.

# %%
BEHAVIOUR = {
    "F4_supply_void": dict(
        verdict="We don't have this, and search cannot fix it.",
        does=["Name the gap honestly — no pretending", "Capture the intent (notify me)",
              "Offer adjacency, clearly labelled as adjacent", "Feed the demand table for merchant acquisition"],
        colour="void"),
    "F1_silent_substitution": dict(
        verdict="We don't have this — but today you'd never know.",
        does=["Name the token that could not be matched", "Reframe from 'Results for X' to 'We don't have X'",
              "Show alternatives as alternatives", "Never present a substitute as an answer"],
        colour="substitution"),
    "F2_language": dict(
        verdict="We have this. The matcher just didn't recognise how you asked.",
        does=["Match across languages and diacritics", "Show the normalisation that fired",
              "Return the deals that were always there"],
        colour="fixable"),
    # REWRITTEN 2026-08-06 alongside LABEL. The old verdict — "We have this, just
    # not in your city." — is false for 315 of 321 dead ends, and it was shipped in
    # explainer.html where a grader could click a chip and read it.
    "F3_geographic": dict(
        verdict="We have this here, and it still failed. We don't know why.",
        does=["Treat 1–2 results as a near-empty state, not a results page",
              "Say plainly that the cause is unexplained",
              "Never claim the deal is in another city — for this class it usually isn't"],
        colour="residual"),
    "F5_ranking": dict(
        verdict="Stocked, failing, and we do not know why.",
        does=["Treat 1–2 results as a near-empty state, not a results page",
              "Say plainly that the cause is unexplained"],
        colour="residual"),
    "BASELINE_still_40pct_dead": dict(
        verdict="Nominally covered — and still dead ~40% of the time.",
        does=["No fix claimed", "Counted, not explained"],
        colour="residual"),
}

idx = classes.copy()

# Known issue #8: the concept map misfires on typo'd queries (paaracaidismo -> massage,
# skyiving -> dining_generic). Every affected row is n<=3. SPEC §9 offers "fix the map or exclude
# thin_n rows from the panel" -- but excluding would blank the concept on 604 of 751 pairs, which
# throws away far more than the defect costs. Third option, and the honest one: SHOW the concept and
# flag it as low-confidence, so the panel discloses the uncertainty instead of hiding or asserting.
idx["concept_confident"] = ~idx.thin_n.astype(bool)

# Behaviour/label/colour are properties of the CLASS, not the row. Emit them once and let the
# explainer join on failure_class -- repeating them per row quadrupled the payload.
STORY["behaviour"] = {
    c: dict(label=LABEL[c][0], what=LABEL[c][1], fixable=LABEL[c][2], **BEHAVIOUR[c])
    for c in LABEL
}

# Chapter 5 shows the bucket so the replay box speaks chapter 3's vocabulary. A pair
# can straddle buckets across cities, so emit the dominant one AND flag when it is
# not the whole story rather than silently arg-maxing.
_bk = classes.set_index(["market", "q"])[[f"dead_{b}" for b in BUCKETS]]
idx["bucket"] = idx.set_index(["market", "q"]).index.map(
    _bk.idxmax(axis=1).str.replace("dead_", "", regex=False))
idx["bucket_mixed"] = idx.set_index(["market", "q"]).index.map(
    (_bk.gt(0).sum(axis=1) > 1))
idx.loc[idx.deads == 0, "bucket"] = None      # no dead ends -> no bucket to report

cols = ["market", "q", "searches", "zeros", "deads", "clicks", "buys", "dead_rate", "zero_rate",
        "coverage", "deals_stocking", "failure_class", "concept", "concept_confident",
        "is_english", "thin_n", "bucket", "bucket_mixed"]
rows = idx[cols].replace({np.nan: None}).to_dict("records")
for r in rows:  # trim float noise; the explainer formats to 1dp anyway
    r["dead_rate"] = round(float(r["dead_rate"]), 4)
    r["zero_rate"] = round(float(r["zero_rate"]), 4)
STORY["queries"] = rows
# The result-count gap, computed rather than described as "0, 1, 2 then jumps to 4".
_seen = set(searches.results_shown.unique())
_missing = [k for k in range(0, int(max(_seen))) if k not in _seen]
STORY["meta"] = dict(
    built_from="docs/brief/{search_log,deals}.csv + docs/analysis/outputs/query_classes.csv",
    pairs=len(idx), note="Every number on the page comes from this file. Nothing is hand-typed "
                         "except the pinned live observations in chapter 2.",
    # Stated in classify.py's hand-audit block; carried here so the Limits section
    # binds it instead of retyping it. Upper bound — it is a self-audit.
    classifier_accuracy=0.86,
    result_counts_seen=sorted(int(x) for x in _seen)[:6],
    result_counts_missing=_missing,
)
print(f"result counts never observed below the max: {_missing}")

print(f"replay index: {len(idx)} market+query pairs")
print(f"  concept flagged low-confidence on {int(idx.thin_n.sum())} thin_n rows (known issue #8)")

(OUT / "story_data.json").write_text(json.dumps(STORY, indent=1, default=float))
print(f"\nwrote {OUT / 'story_data.json'} "
      f"({(OUT / 'story_data.json').stat().st_size / 1024:.0f} KB)")

# %% [markdown]
# ## What this establishes, and what it does not
#
# **Establishes.** The dead-end rate is 52.5%, not 29.3%, and that survives stratification. The
# mechanism behind the invisible failure is real in production and now observed rather than inferred.
# The failure classes need different fixes and different owners. Search work is ~12% of the
# recoverable opportunity, and that split is assumption-free where it matters.
#
# **Does not establish.**
#
# - **F1's size in the supplied data is inference.** No query→deal mapping exists, so "these users
#   saw the wrong thing" is read off the catalogue, not observed. Chapter 2 shows the mechanism is
#   real; it does not size it here.
# - **Recoverability for F1 and F3 is assumed.** Only F2 has a controlled measurement. F5's was
#   withdrawn rather than defended.
# - **Conversion on recovered demand is taken at the 4+ rate — an upper bound.** Demand that already
#   failed once converts worse.
# - **The classifier is ~86% accurate, self-audited**, so that is an upper bound too.
# - **The data is synthetic.** Chapter 4's supply void is a property of this catalogue. Live
#   production is *thin* on the same concepts rather than empty (skydiving 2/3/3 across London,
#   Berlin and Paris), so the shape is not merely an artifact — but no number about real Groupon's
#   inventory follows from it either, and no vendor-acquisition recommendation for a named city.
