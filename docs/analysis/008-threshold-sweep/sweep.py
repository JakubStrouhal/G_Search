"""Calibrate the abstention threshold against Part A's labelled pairs.

    .venv/bin/python docs/analysis/008-threshold-sweep/sweep.py

001-part-b/SPEC.md §6, §10 step 4. This is the step that gates all UI work: every
screen assumes the system can tell "we stock something for this" from "we stock
nothing", and this measures whether it can.

GROUND TRUTH is `query_classes.coverage`, produced by classify.py independently of
any embedding:

    absent               437 pairs   the market stocks nothing -> MUST abstain
    stocked + plausible  314 pairs   something exists          -> must not abstain

`absent` decomposes exactly into F4 (178) + F1 (259) — the spine's `nowhere`
bucket. Calibrating on F4 alone would train the threshold to abstain on supply
voids while passing all 259 silent-substitution rows, which is the one failure
this prototype exists to fix.

TWO ERRORS, REPORTED SEPARATELY AND NEVER BLENDED:

    false-confident   an `absent` pair scores >= LOW. The system shows results for
                      something the catalogue does not have. THIS IS F1. Expensive.
    false-abstain     a `stocked` pair scores < LOW. The system says "we don't have
                      it" when it does. Annoying, but honest.

A single accuracy number would hide which mistake is being made, and the whole
argument of this package is that those two mistakes are not equivalent.

ONLY `LOW` IS CALIBRATED HERE, AND THAT IS A REAL LIMIT. `LOW` separates abstain
from show, and `coverage` is exactly that label. `HIGH` separates "confident
results" from "labelled adjacency" — a PRESENTATION choice for which this dataset
carries no ground truth at all. Hand-picking HIGH and calling it calibrated would
be the fitting this whole exercise exists to avoid, so it is reported as a
judgement, explicitly.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(exist_ok=True)
DB = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

# Max cosine per (market, q), scored against THAT MARKET's services only — D-A:
# market is a structured filter and lives in the join, never in the vector.
SQL = """
select qc.market, qc.q, qc.coverage, qc.failure_class, qc.searches, qc.deads, qc.thin_n,
       max(1 - (qe.embedding <=> se.embedding))                       as max_sim,
       (array_agg(s.title order by qe.embedding <=> se.embedding))[1] as nearest_title
from query_classes qc
join query_embeddings   qe on qe.q = qc.q
join services            s on s.market = qc.market
join service_embeddings se on se.service_id = s.service_id
group by qc.market, qc.q, qc.coverage, qc.failure_class, qc.searches, qc.deads, qc.thin_n
"""

with psycopg.connect(DB) as conn:
    rows = conn.execute(SQL).fetchall()
    cols = [d[0] for d in conn.execute(SQL).description]
df = pd.DataFrame(rows, columns=cols)
if len(df) != 751:
    sys.exit(f"ABORT — expected 751 labelled pairs, got {len(df)}. Re-run build_embeddings.py.")

GRID = np.round(np.arange(0.00, 1.001, 0.005), 3)


def sweep(frame, plausible_as):
    """Error rates across the grid under one reading of the contested tier."""
    if plausible_as == "stocked":
        d = frame
    elif plausible_as == "excluded":
        d = frame[frame.coverage != "plausible"]
    else:                                  # confident_only: drop the thin_n labels
        d = frame[~frame.thin_n]
    absent, stocked = d[d.coverage == "absent"], d[d.coverage != "absent"]
    out = []
    for low in GRID:
        fc = absent[absent.max_sim >= low]      # shown when nothing exists  -> F1
        fa = stocked[stocked.max_sim < low]     # abstained when it existed
        out.append(dict(
            low=low,
            false_confident=len(fc) / len(absent),
            false_abstain=len(fa) / len(stocked),
            fc_searches=fc.searches.sum() / absent.searches.sum(),
            fa_searches=fa.searches.sum() / stocked.searches.sum(),
            n_absent=len(absent), n_stocked=len(stocked)))
    return pd.DataFrame(out)


print(f"{len(df)} labelled pairs scored\n")
print(df.groupby("coverage").max_sim.describe()[["count", "mean", "25%", "50%", "75%"]].round(3).to_string())

# THE DECOMPOSITION THAT CHANGES HOW EVERY NUMBER BELOW IS READ.
#
# `thin_n` flags a low-confidence concept assignment, n<=3 (INDEX.md #8) — 604 of
# 751 pairs, but only ~10% of search volume, because they are overwhelmingly
# one-off typos. Inspecting the named failures showed the expensive error is
# almost entirely THERE, and that the model is usually RIGHT where the label
# says it is wrong: FR 'sallee de sport' -> 'Abonnement Salle de Sport' is scored
# as a false-confident because classify.py could not map the typo to `gym` and so
# tagged the row `absent`. The embedding did the correct thing.
#
# So the raw rate partly measures a known defect in the ground truth, not the
# retrieval. BOTH populations are published: leading with the flattering subset
# would be exactly the fitting this sweep exists to avoid.
print("\n" + "=" * 74)
print("LABEL-CONFIDENCE DECOMPOSITION (thin_n = concept assigned at n<=3, INDEX #8)")
for name, sub in (("confident label", df[~df.thin_n]), ("thin_n (n<=3)", df[df.thin_n])):
    print(f"  {name:16} {len(sub):4d} pairs  {sub.searches.sum():5,d} searches "
          f"({sub.searches.sum() / df.searches.sum():5.1%} of volume)")

results = {}
for arm in ("stocked", "excluded", "confident_only"):
    s = sweep(df, arm)
    results[arm] = s
    s.to_csv(OUT / f"sweep_plausible_{arm}.csv", index=False)

    # Separability, independent of where the line is put. AUC is reported because
    # it answers "is there a signal at all", which is the question that decides
    # whether SPEC §1's top MUST is reachable — not "which threshold to ship".
    d = (df if arm == "stocked"
         else df[df.coverage != "plausible"] if arm == "excluded"
         else df[~df.thin_n])
    a, b = d[d.coverage == "absent"].max_sim.values, d[d.coverage != "absent"].max_sim.values
    auc = np.mean([(x < y) + 0.5 * (x == y) for x in a for y in b])

    # Three candidate operating points, each an explicit editorial choice.
    s = s.assign(youden=1 - s.false_confident - s.false_abstain)
    best = s.loc[s.youden.idxmax()]
    strict = s[s.false_confident <= 0.10].iloc[0] if (s.false_confident <= 0.10).any() else None

    print(f"\n{'='*74}\nplausible counted as: {arm.upper()}   "
          f"(absent {int(s.n_absent.iloc[0])} vs stocked {int(s.n_stocked.iloc[0])})")
    print(f"  AUC (separability, 0.5 = none): {auc:.3f}")
    print(f"  balanced point  LOW={best.low:.3f}  "
          f"false-confident {best.false_confident:6.1%}  false-abstain {best.false_abstain:6.1%}")
    if strict is not None:
        print(f"  <=10% F1 point  LOW={strict.low:.3f}  "
              f"false-confident {strict.false_confident:6.1%}  false-abstain {strict.false_abstain:6.1%}")
    print("\n  LOW    false-confident (F1)   false-abstain   [by searches: fc / fa]")
    for low in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55):
        r = s[s.low == low].iloc[0]
        print(f"  {low:.2f}   {r.false_confident:14.1%} {r.false_abstain:15.1%}"
              f"   [{r.fc_searches:.1%} / {r.fa_searches:.1%}]")

# The failing pairs at the balanced point, named — "here are the failures" is the
# half of the deliverable that makes the rate checkable rather than assertable.
s = results["stocked"].assign(youden=lambda x: 1 - x.false_confident - x.false_abstain)
low = float(s.loc[s.youden.idxmax()].low)
fc = df[(df.coverage == "absent") & (df.max_sim >= low)].sort_values("max_sim", ascending=False)
fa = df[(df.coverage != "absent") & (df.max_sim < low)].sort_values("max_sim")
fc.to_csv(OUT / "failures_false_confident.csv", index=False)
fa.to_csv(OUT / "failures_false_abstain.csv", index=False)

print(f"\n{'='*74}\nNAMED FAILURES at LOW={low:.3f} (plausible as stocked)")
print(f"\nfalse-confident — absent, yet shown ({len(fc)} pairs, {fc.searches.sum():,} searches). Worst 8:")
for r in fc.head(8).itertuples(index=False):
    print(f"  {r.max_sim:.3f}  {r.market} {r.q!r:34} [{r.failure_class.split('_')[0]}] -> {r.nearest_title!r}")
print(f"\nfalse-abstain — stocked, yet refused ({len(fa)} pairs, {fa.searches.sum():,} searches). Worst 6:")
for r in fa.head(6).itertuples(index=False):
    print(f"  {r.max_sim:.3f}  {r.market} {r.q!r:34} [{r.coverage}] -> {r.nearest_title!r}")

df.to_csv(OUT / "pair_similarities.csv", index=False)
print(f"\nwrote {OUT.relative_to(ROOT)}/ — sweep_plausible_*.csv, failures_*.csv, pair_similarities.csv")
