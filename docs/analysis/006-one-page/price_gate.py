"""Does gating a cross-city offer on price rescue it?

The proposal: when the answering deal sits in another city, offer the trip — but only
when the deal is expensive enough that travelling is worth it (">$100").

The rule is sound. This script asks whether *this catalogue* can pay it off, and the
answer is no, for a reason that is itself the finding: the concepts whose price would
justify a trip are the ones the catalogue stocks nothing for.

Imports STOCK_TITLE from classify.py rather than restating it — the repo already carries
two hand-built CONCEPTS maps that can drift (CLAUDE.md), and a third copy here would be
a third thing to keep in sync.

    python3 docs/analysis/006-one-page/price_gate.py
"""
import contextlib
import importlib.util
import io
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUTPUTS = ROOT / "docs" / "analysis" / "outputs"

# classify.py prints its whole report on import; swallow it, we only want the map.
_spec = importlib.util.spec_from_file_location("cl", ROOT / "docs" / "analysis" / "classify.py")
_cl = importlib.util.module_from_spec(_spec)
with contextlib.redirect_stdout(io.StringIO()):
    _spec.loader.exec_module(_cl)

STOCK_TITLE, deals = _cl.STOCK_TITLE, _cl.deals
loc = pd.read_csv(OUTPUTS / "inventory_location.csv")

TOTAL_DEAD = 4720          # FINDINGS.md §5f denominator, one denominator for every share
THRESHOLD = 100.0          # USD — the proposed "worth the trip" gate

titles = deals["title"].str.lower()
another = loc[loc["inventory_location"] == "another_city"]

priced = generous = strict = 0
per_concept: dict[str, int] = {}

for concept, pattern in STOCK_TITLE.items():
    stocking = deals[titles.str.contains(pattern, regex=True, na=False)]
    for _, row in another[another["concept"] == concept].iterrows():
        # The answering deals: same market, any city that is not the searcher's.
        elsewhere = stocking[(stocking["market"] == row["market"]) & (stocking["city"] != row["city"])]
        if elsewhere.empty:
            continue
        priced += row["deads"]
        per_concept[concept] = per_concept.get(concept, 0) + int(row["deads"])
        if (elsewhere["price_usd"] > THRESHOLD).any():
            generous += row["deads"]                       # at least one is expensive
        if elsewhere["price_usd"].median() > THRESHOLD:
            strict += row["deads"]                         # the typical one is expensive


def share(n):
    return f"{n:5d}  = {100 * n / TOTAL_DEAD:.2f}% of all {TOTAL_DEAD:,} dead ends"


print(f"another_city dead ends            : {share(int(another['deads'].sum()))}")
print(f"  ...with a priced alternative    : {share(int(priced))}")
print()
print(f"GENEROUS  >=1 answering deal >${THRESHOLD:.0f} : {share(int(generous))}")
print(f"STRICT    median answering >${THRESHOLD:.0f}   : {share(int(strict))}")
print()
print("composition, dead ends by concept :",
      dict(sorted(per_concept.items(), key=lambda kv: -kv[1])))
print(f"catalogue price ceiling           : ${deals['price_usd'].max():.2f} — nothing costs more")
print()
print("Read: the gate is a sound rule and this catalogue cannot pay it off. The concepts")
print("whose price would justify a trip — skydiving, helicopter, ballooning — have ZERO")
print("deals (the supply void). What it does stock one city over is haircuts and gyms.")
