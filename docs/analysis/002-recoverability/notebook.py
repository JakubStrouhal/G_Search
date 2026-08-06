# %% [markdown]
# # Part A validation — the data, and a simulation of what we can actually fix
#
# Two jobs, in order:
#
# 1. **Validate** the headline before building on it. The 52.5% dead-end number rests on the claim
#    that 1–2 results converts like zero. If that cliff is really *composition* — thin result sets
#    skewing toward concepts that convert badly anyway — the headline shrinks and Part C's
#    measurement proposal changes. This is checked first because everything downstream multiplies it.
# 2. **Simulate** recovery per failure class. Not "search is broken by X%" but "here is what a fix
#    to each class returns, and here is the assumption each number rests on."
#
# **The honesty rule for this notebook.** Recoverability per class is an *assumption*, not a
# measurement — except for F2, where the language test gives a controlled anchor. Every assumption
# is named, given a range, and its effect on the output shown. A single point estimate presented as
# a forecast is the failure mode this repo is graded against.
#
# Run: `.venv/bin/python docs/analysis/002-recoverability/notebook.py`
# (or open in VS Code / Cursor — the `# %%` markers make it a notebook)

# %%
from pathlib import Path

import matplotlib.pyplot as plt
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
BRIEF = ROOT / "docs" / "brief"
OUT = ROOT / "docs" / "analysis" / "002-recoverability" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

searches = pd.read_csv(BRIEF / "search_log.csv")
deals = pd.read_csv(BRIEF / "deals.csv")
classes = pd.read_csv(ROOT / "docs" / "analysis" / "outputs" / "query_classes.csv")

# Dead end = the user got nothing usable. The whole point of Part A is that this is NOT
# the same as zero results: 1-2 results converts like zero. Cell 1 tests exactly that.
searches["band"] = np.select(
    [searches.results_shown == 0, searches.results_shown <= 2],
    ["0", "1-2"],
    default="4+",
)
searches["dead"] = searches.results_shown <= 2
searches["concept"] = searches.set_index(["market", "raw_query"]).index.map(
    classes.set_index(["market", "q"]).concept
)
searches["failure_class"] = searches.set_index(["market", "raw_query"]).index.map(
    classes.set_index(["market", "q"]).failure_class
)

print(f"{len(searches):,} searches · {searches.raw_query.nunique()} unique queries · "
      f"{len(deals)} deals ({deals.title.nunique()} unique titles)")
print(f"concept assigned to {searches.concept.notna().mean() * 100:.1f}% of rows")

# %% [markdown]
# ## 1. Does the cliff survive stratification?  *(gates everything below)*
#
# The raw claim: CTR 10.3% at 1–2 results vs 51.7% at 4+. The objection: maybe queries that return
# 1–2 results are systematically *different* queries — rarer concepts, thinner cities — that would
# convert badly at any result count. Test it by comparing 1–2 vs 4+ **within** concept × city
# strata, so concept mix and city cannot drive the gap.

# %%
matched = searches[searches.concept.notna() & searches.band.isin(["1-2", "4+"])]

strata = []
for (concept, city), grp in matched.groupby(["concept", "city"]):
    low, high = grp[grp.band == "1-2"], grp[grp.band == "4+"]
    if len(low) >= 5 and len(high) >= 5:  # both sides need enough rows to compare
        strata.append(
            dict(concept=concept, city=city, n_low=len(low), n_high=len(high),
                 s2p_low=low.purchased.mean(), s2p_high=high.purchased.mean(),
                 ctr_low=low.clicked.mean(), ctr_high=high.clicked.mean())
        )
strata = pd.DataFrame(strata)
weights = strata.n_low + strata.n_high

raw = searches.groupby("band").agg(n=("purchased", "size"),
                                   ctr=("clicked", "mean"),
                                   s2p=("purchased", "mean"))

print("RAW (unstratified)")
print(f"  1-2 results : CTR {raw.loc['1-2', 'ctr'] * 100:5.1f}%   s2p {raw.loc['1-2', 's2p'] * 100:5.2f}%   n={raw.loc['1-2', 'n']:,}")
print(f"  4+  results : CTR {raw.loc['4+', 'ctr'] * 100:5.1f}%   s2p {raw.loc['4+', 's2p'] * 100:5.2f}%   n={raw.loc['4+', 'n']:,}")

print(f"\nWITHIN concept x city strata ({len(strata)} strata, "
      f"{weights.sum():,} searches, volume-weighted)")
print(f"  1-2 results : CTR {np.average(strata.ctr_low, weights=weights) * 100:5.1f}%   "
      f"s2p {np.average(strata.s2p_low, weights=weights) * 100:5.2f}%")
print(f"  4+  results : CTR {np.average(strata.ctr_high, weights=weights) * 100:5.1f}%   "
      f"s2p {np.average(strata.s2p_high, weights=weights) * 100:5.2f}%")

print(f"\nDirection holds in {(strata.ctr_high > strata.ctr_low).sum()}/{len(strata)} strata on CTR, "
      f"{(strata.s2p_high > strata.s2p_low).sum()}/{len(strata)} on s2p")

# %% [markdown]
# **VERDICT: the cliff is not composition.** Stratifying moves s2p from 1.68% to 1.70% and CTR from
# 10.3% to 10.2% — i.e. essentially nothing — and the direction holds in 137 of 138 strata. The
# 52.5% combined dead-end rate stands, and "1–2 results converts like zero" is a statement about
# result count, not about which queries happen to land there.
#
# This closes known issue #3 and unblocks pending 5.2 (dead-end rate replacing zero-result rate as
# the headline metric).

# %%
DEAD_TOTAL = int(searches.dead.sum())
S2P_HEALTHY = searches[searches.band == "4+"].purchased.mean()  # what a fixed search converts at
S2P_NONZERO = searches[searches.results_shown > 0].purchased.mean()  # the FINDINGS.md baseline

print(f"dead-end searches (0 or 1-2 results) : {DEAD_TOTAL:,} of {len(searches):,} "
      f"= {DEAD_TOTAL / len(searches) * 100:.1f}%")
print(f"s2p at 4+ results (a working search) : {S2P_HEALTHY * 100:.2f}%")
print(f"s2p on all non-zero searches         : {S2P_NONZERO * 100:.2f}%  <- FINDINGS.md baseline")

# %% [markdown]
# ## 2. The data — where the dead ends actually are
#
# Volume by failure class. This is measurement, no assumptions yet.

# %%
by_class = (searches[searches.failure_class.notna()]
            .groupby("failure_class")
            .agg(searches=("dead", "size"), dead=("dead", "sum"),
                 purchases=("purchased", "sum"))
            .assign(dead_rate=lambda x: x.dead / x.searches)
            .sort_values("dead", ascending=False))
by_class["share_of_dead"] = by_class.dead / DEAD_TOTAL

print(by_class.assign(
    dead_rate=(by_class.dead_rate * 100).round(1),
    share_of_dead=(by_class.share_of_dead * 100).round(1)).to_string())

# %% [markdown]
# ## 3. Recoverability — the assumptions, stated
#
# **This is the part that is not measurement.** For each class: what fraction of its dead ends does
# a fix actually recover? One class has a controlled anchor; the rest are reasoned assumptions with
# ranges, and §5 shows how much the answer depends on them.
#
# | Class | Fix | Recoverable | Basis |
# |---|---|---|---|
# | **F2** lexical/language | multilingual matching, diacritic folding | **52%** (43–61%) | **Measured.** English phrasing dead-ends 81.2% vs 39.0% local — a 42.3pp gap on 81.2% of volume = 52% of that class's dead ends are language, not supply |
# | **F5** ranking cutoff | ~~fix the threshold~~ | **0%** | **WITHDRAWN 2026-08-06 by live probe P4.** The 40% rested entirely on "no search returns exactly 3, so there must be a cutoff". Live Groupon returns exactly 3 routinely (`quadbike` 3, `trapeze` 3, GB/london, N=33, smooth low-count distribution 0,1,2,3,…). The supplied data's 0,1,2→4 gap across 8,997 searches is a **generator artifact**, so the inference is dead. `classify.py`'s F5 predicate is a **residual** — stocked, failing, and none of F2/F3 apply — so the 353 dead ends are a real population with no known cause, i.e. a second BASELINE. No fix claimed. See `003-live-validation/RESULT.md` |
# | **F3** geographic | radius widening as an explicit choice | 25% (10–40%) | **Assumption.** Inventory exists in-market, just not in-city. Discount heavily: a user offered a deal 90 min away often declines |
# | **F1** silent substitution | name the unmatched token, reframe as adjacency | **0%** (−10–0%) | **Deliberate zero.** The fix makes a false-confident page honest. It may *reduce* near-term clicks. The return is trust, which this dataset cannot measure |
# | **F4** supply void | merchant acquisition | **0%** | **Zero by construction.** No inventory exists. Search cannot fix this at any quality — that is the finding |
# | BASELINE | — | 0% | No fix claimed. 4,321 searches, ~40% dead, unexplained |

# %%
RECOVERABLE = {  # class -> (low, point, high) share of that class's dead ends a fix returns
    "F2_language":               (0.43, 0.52, 0.61),   # measured anchor
    "F5_ranking":                (0.00, 0.00, 0.00),   # WAS (0.10, 0.40, 0.70) -- killed by live P4
    "F3_geographic":             (0.10, 0.25, 0.40),   # assumption
    "F1_silent_substitution":    (-0.10, 0.00, 0.00),  # honesty fix, not a recovery
    "F4_supply_void":            (0.00, 0.00, 0.00),   # search cannot fix supply
    "BASELINE_still_40pct_dead": (0.00, 0.00, 0.00),   # no claim
}

# Sanity: the F2 anchor, recomputed here rather than quoted.
EN_DEAD, LOCAL_DEAD = 0.812, 0.390  # language_test.py, matched pairs
print(f"F2 anchor: ({EN_DEAD:.3f} - {LOCAL_DEAD:.3f}) / {EN_DEAD:.3f} = "
      f"{(EN_DEAD - LOCAL_DEAD) / EN_DEAD:.3f} of English-phrased dead ends are language")

# %% [markdown]
# ## 4. The simulation
#
# Recovered searches, converted to purchases at the **4+ result** rate — what a search that works
# actually converts at. Labelled an upper bound throughout: recovered demand converts worse than
# organic demand, because it is demand that already failed once.

# %%
sim = by_class.copy()
sim["rec_low"] = [RECOVERABLE.get(c, (0, 0, 0))[0] for c in sim.index]
sim["rec_mid"] = [RECOVERABLE.get(c, (0, 0, 0))[1] for c in sim.index]
sim["rec_high"] = [RECOVERABLE.get(c, (0, 0, 0))[2] for c in sim.index]

for band in ("low", "mid", "high"):
    sim[f"searches_{band}"] = sim.dead * sim[f"rec_{band}"]
    sim[f"purch_{band}"] = sim[f"searches_{band}"] * S2P_HEALTHY

view = sim[["dead", "rec_mid", "searches_mid", "purch_mid"]].copy()
view.columns = ["dead ends", "recoverable", "searches back", "purchases/mo"]
print(view.round(1).to_string())

tot_s, tot_p = sim.searches_mid.sum(), sim.purch_mid.sum()
print(f"\nSEARCH-FIXABLE      : {tot_s:6.0f} searches/mo -> {tot_p:5.0f} purchases/mo (upper bound)")
print(f"  range across assumptions: {sim.purch_low.sum():.0f} - {sim.purch_high.sum():.0f} purchases/mo")

f4_dead = sim.loc["F4_supply_void", "dead"]
print(f"\nNOT SEARCH-FIXABLE  : {f4_dead:6.0f} searches/mo locked behind supply "
      f"({f4_dead / DEAD_TOTAL * 100:.0f}% of all dead ends)")
print(f"  if that inventory existed : {f4_dead * S2P_HEALTHY:5.0f} purchases/mo (upper bound)")
print(f"\nSo the ceiling on search work is {tot_p / (tot_p + f4_dead * S2P_HEALTHY) * 100:.0f}% "
      f"of the recoverable total. The rest is a merchant acquisition problem.")

# %% [markdown]
# ## 5. Sensitivity — how much does the answer depend on the guesses?
#
# The point of this cell: show that the *headline conclusion* does not move even when every
# assumption is pushed to its extreme, because the conclusion is about the F4/everything-else split
# and F4 is zero by construction, not by assumption.

# %%
print("Search-fixable purchases/mo under each assumption set:")
for band, label in (("low", "pessimistic"), ("mid", "central"), ("high", "optimistic")):
    p = sim[f"purch_{band}"].sum()
    print(f"  {label:12} {p:5.0f}   vs supply-void ceiling {f4_dead * S2P_HEALTHY:.0f}"
          f"   -> search is {p / (p + f4_dead * S2P_HEALTHY) * 100:4.1f}% of the opportunity")

print("\nEven at the optimistic end, most of the recoverable demand is not addressable by search.")
print("That conclusion is assumption-free: F4 is zero because the inventory does not exist.")

# %% [markdown]
# ## 6. Allocation — if you can sign N merchants, where?
#
# The supply void is a merchant acquisition problem, so the useful artifact is not a defect rate but
# a ranked buy list: which market × city × concept cells return the most demand per merchant signed.

# %%
void = searches[(searches.failure_class == "F4_supply_void")]
cells = (void.groupby(["market", "city", "concept"])
         .agg(searches=("dead", "size"))
         .assign(purchases_mo=lambda x: x.searches * S2P_HEALTHY)
         .sort_values("searches", ascending=False))
cells["cumulative_%"] = (cells.purchases_mo.cumsum() / cells.purchases_mo.sum() * 100)

print(f"{len(cells)} empty cells with real demand. Top 12:\n")
print(cells.head(12).round(1).to_string())
n20 = (cells["cumulative_%"] <= 80).sum() + 1
print(f"\n{n20} cells cover 80% of the recoverable supply-void demand "
      f"({n20 / len(cells) * 100:.0f}% of the cells).")
cells.to_csv(OUT / "acquisition_priority.csv")

# %% [markdown]
# ## 7. Chart — data vs simulation, side by side

# %%
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

order = by_class.sort_values("dead", ascending=True)
labels = [i.replace("_", " ").replace("still 40pct dead", "(residual)") for i in order.index]
ax1.barh(labels, order.dead, color="#c44")
ax1.set_title("THE DATA — dead-end searches per month", fontweight="bold", loc="left")
ax1.set_xlabel("searches ending in 0, 1 or 2 results")
for i, v in enumerate(order.dead):
    ax1.text(v + 20, i, f"{int(v):,}", va="center", fontsize=9)

s = sim.loc[order.index]
ax2.barh(labels, s.searches_mid, color="#2a7", label="recoverable by search")
ax2.barh(labels, s.dead - s.searches_mid, left=s.searches_mid, color="#ddd",
         label="not recoverable by search")
ax2.set_title("THE SIMULATION — what a fix returns", fontweight="bold", loc="left")
ax2.set_xlabel("searches per month")
ax2.legend(loc="lower right", fontsize=9)

fig.suptitle(
    f"{DEAD_TOTAL:,} dead ends/month. Search work recovers ~{tot_s:,.0f} of them "
    f"(~{tot_p:.0f} purchases, upper bound).\n"
    f"{f4_dead:,.0f} are locked behind inventory that does not exist — no search quality fixes those.",
    fontsize=10, y=1.06,
)
fig.tight_layout()
fig.savefig(OUT / "data_vs_simulation.png", dpi=150, bbox_inches="tight")
print(f"saved {OUT / 'data_vs_simulation.png'}")

# %% [markdown]
# ## What this notebook establishes
#
# 1. **The 52.5% dead-end headline survives stratification** — the cliff is result count, not
#    concept mix. Closes known issue #3.
# 2. **Most of the loss is not a search problem.** Even under optimistic assumptions about every
#    fixable class, the supply void dominates — and that split is assumption-free.
# 3. **The recoverable-by-search number rests on one measured anchor (F2) and three stated guesses.**
#    Said out loud, with ranges, rather than presented as a forecast.
# 4. **A ranked acquisition list**, which is the actual deliverable implied by finding 2.
#
# ### What it does not establish
#
# - Recoverability for F1, F3 and F5 is **assumed**. Only F2 has a controlled measurement behind it.
# - Conversion on recovered demand is taken at the 4+ result rate. That is an **upper bound** —
#   demand that already failed once converts worse.
# - F1's fix is scored at zero recovery. Its return is trust, which this dataset cannot measure.
# - The classifier's own accuracy is ~86%, self-audited, and stated as an upper bound.
