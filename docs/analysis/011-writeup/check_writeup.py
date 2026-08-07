"""Every number in Part C must resolve to a source, or this exits 1.

    python3 docs/analysis/011-writeup/check_writeup.py

WHY THIS EXISTS. Part C is prose, and prose is exactly where this package has
already been caught drifting: FINDINGS.md §9 row 12 is a figure that was correct
in a table and stale in a sentence eleven lines away. CLAUDE.md's rule is "re-run
the script before quoting any number"; a rule is a discipline, and
supabase/check_descriptions.py is the repo's precedent for turning a discipline
into a test. This is the same move applied to the writeup.

WHAT IT CHECKS. Every numeric token in WRITEUP.md that looks like a *claim* must
either equal a figure this script recomputes from the committed data, or appear
in ALLOWLIST with the file that owns it named. An unresolved number FAILS.

    It fails rather than skips, and that is the whole design. Corrections
    register entry 5 in this very package is an acceptance check that passed on
    nothing, because its inputs silently did not match anything. A verifier for
    the honesty deliverable is the last place that mistake may be repeated.

WHICH TOKENS COUNT AS CLAIMS (stated, because any rule here excludes something):
a number is checked if it carries a %, a $, a decimal point or a thousands
comma, or if it is an integer >= 10. Small bare integers are prose -- "1-2
results", "three conventions" -- and the writeup spells out the ones that are
load-bearing ("five markets", "twenty cities", "six render states"). Literal
strings in EXEMPT_LITERALS are removed before extraction.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WRITEUP = HERE / "WRITEUP.md"
OUT = ROOT / "docs" / "analysis" / "outputs"

# Substrings removed before extraction: they are not quantities.
EXEMPT_LITERALS = ["8:01", "1h50m", "MiniLM-L12-v2", "[43.2%, 64.7%]"]

# ---------------------------------------------------------------------------
# FACTS -- recomputed here, never transcribed.
# ---------------------------------------------------------------------------
facts: dict[float, str] = {}


def fact(value, source):
    """Register a figure at every precision it could honestly be quoted at.

    1 to 4 decimal places, plus the bare integer when the value already is one.
    Deliberately NOT 0 dp for a fractional value: registering 43 for 43.2 would
    let a wrong number pass by being close, which is the opposite of the job.
    """
    value = float(value)
    keys = {round(value, n) for n in (1, 2, 3, 4)}
    if abs(value - round(value)) < 1e-9:
        keys.add(round(value))
    for k in keys:
        facts.setdefault(k, source)


log = pd.read_csv(ROOT / "docs" / "brief" / "search_log.csv")
deals = pd.read_csv(ROOT / "docs" / "brief" / "deals.csv")

fact(len(log), "search_log.csv rows")
fact(log.raw_query.nunique(), "search_log.csv unique raw_query")
fact(len(deals), "deals.csv rows")
fact(deals.title.nunique(), "deals.csv unique titles")
fact(deals.price_usd.max(), "deals.csv max price_usd")
fact(log.purchased.sum(), "search_log.csv total purchases")

zero = log.results_shown == 0
near = log.results_shown.between(1, 2)
plenty = log.results_shown >= 4
fact(zero.mean() * 100, "zero-result share")
fact(near.mean() * 100, "1-2 result share")
fact((zero | near).mean() * 100, "dead-end share (<=2)")
fact(log[near].purchased.mean() * 100, "search->purchase at 1-2")
fact(log[plenty].purchased.mean() * 100, "search->purchase at 4+")

qc = pd.read_csv(OUT / "query_classes.csv")
total_dead = qc.deads.sum()
fact(len(qc), "query_classes.csv rows")
fact(total_dead, "total dead ends")
for col, label in [
    ("dead_nowhere", "nowhere"),
    ("dead_same_city", "same city"),
    ("dead_another_city", "another city"),
    ("dead_cant_tell", "can't tell"),
]:
    fact(qc[col].sum(), f"inventory_location {label} (count)")
    fact(qc[col].sum() / total_dead * 100, f"inventory_location {label} (share)")

f4 = qc[qc.failure_class == "F4_supply_void"]
fact(len(f4), "F4 supply-void pairs (classify.py)")
fact(f4.searches.sum(), "F4 supply-void searches (classify.py)")

# The another_city composition, so the "nobody drives for a haircut" line is data.
comp = qc.groupby("concept")["dead_another_city"].sum()
for concept, n in comp[comp > 0].items():
    fact(n, f"another_city dead ends, concept {concept}")

sens = pd.read_csv(OUT / "inventory_sensitivity.csv")
for _, row in sens.iterrows():
    fact(row.nowhere / row.total_dead * 100, f"nowhere share, plausible={row.plausible_counts_as}")
    fact(row.same_city / row.total_dead * 100, f"same_city share, plausible={row.plausible_counts_as}")

lp = pd.read_csv(OUT / "language_pairs.csv")
en_n, lo_n = lp.en_n.sum(), lp.loc_n.sum()
en_d = (lp.en_n * lp.en_dead).round().sum()
lo_d = (lp.loc_n * lp.loc_dead).round().sum()
fact(len(lp), "language_pairs.csv matched pairs")
fact((lp.gap_pp > 0).sum(), "language pairs pointing the same way")
fact(en_d / en_n * 100, "English-phrasing dead-end rate")
fact(lo_d / lo_n * 100, "local-phrasing dead-end rate")
fact((en_d / en_n - lo_d / lo_n) * 100, "language gap (pp)")

sweep = json.loads((ROOT / "docs" / "analysis" / "008-threshold-sweep" /
                    "outputs" / "summary.json").read_text())
fact(sweep["auc_all"], "sweep AUC, all labels")
fact(sweep["auc_confident"], "sweep AUC, confident labels")
fact(sweep["confident_pairs"], "sweep confident-label pairs")
fact(sweep["confident_volume_share"] * 100, "sweep confident-label volume share")
fact(sweep["fc_searches"] * 100, "false-confident by search volume")
fact(sweep["fa_searches"] * 100, "false-abstain by search volume")

# ---------------------------------------------------------------------------
# ALLOWLIST -- numbers whose owning artifact is not under docs/analysis/outputs/.
# Each one names where it comes from. Keep this list short; a long allowlist is
# this check quietly turning back into a discipline.
# ---------------------------------------------------------------------------
ALLOWLIST = {
    12: "002-recoverability/README.md -- search's share of recoverable opportunity (11.8%, ~12%)",
    36: "002-recoverability/README.md -- central estimate, purchases per month",
    271: "002-recoverability/README.md -- supply-void ceiling, +271 (+37.5%)",
    7.8: "FINDINGS.md 5f -- tightened recoverability, demonstrable-answer rows only",
    5.7: "FINDINGS.md 5f -- tightened recoverability, F3 additionally withdrawn",
    1.9: "FINDINGS.md 4 -- strict typo bound, validate.py Layer 4",
    44.0: "language_test.py loanword control (printed, not written to the CSV)",
    53.3: "language_test.py rarity control (printed, not written to the CSV)",
    138: "002-recoverability/notebook.py cell 1 -- concept x city strata",
    137: "002-recoverability/notebook.py cell 1 -- strata holding on CTR",
    0.02: "002-recoverability/notebook.py cell 1 -- stratified shift in search->purchase (pp)",
    355: "FINDINGS.md 5f -- same-city failures with a named mechanism (F2 197 + F3 158)",
    1165: "FINDINGS.md 5f -- same-city failures that are stocked, failing and unexplained",
    185: "validate.py Layer 2 -- the alternative always-zero rule, quoted AS the alternative",
    1691: "validate.py Layer 2 -- searches under that alternative rule",
    2.88: "006-one-page/price_gate.py -- generous >$100 cross-city gate",
    0.38: "006-one-page/price_gate.py -- strict >$100 cross-city gate",
    100: "006-one-page/price_gate.py -- the proposed travel threshold, in USD",
    0.6: "009-access-gate/RESULT.md -- logged agent hours for that unit",
    50: "010-screens/RESULT.md -- agent execution, 1h50m across two lanes",
}

# ---------------------------------------------------------------------------
text = WRITEUP.read_text(encoding="utf-8")
# Drop YAML front matter: its dates are metadata, not claims about the data.
if text.startswith("---"):
    text = text.split("\n---\n", 1)[-1]
for literal in EXEMPT_LITERALS:
    text = text.replace(literal, " ")

TOKEN = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")

seen, unresolved = [], []
for raw in TOKEN.findall(text):
    has_marker = raw.startswith("$") or raw.endswith("%") or "." in raw or "," in raw
    value = float(raw.strip("$%").replace(",", ""))
    if not has_marker and value < 10:
        continue
    key = round(value, 4)
    if key in facts:
        seen.append((raw, "computed", facts[key]))
    elif key in ALLOWLIST:
        seen.append((raw, "allowlist", ALLOWLIST[key]))
    else:
        unresolved.append(raw)

words = len(re.findall(r"\S+", text.split("## The log")[0]))
print(f"{WRITEUP.relative_to(ROOT)} -- {words} words before the log")
print(f"recomputed {len(facts)} figures from source; allowlist holds {len(ALLOWLIST)}")
print(f"checked {len(seen) + len(unresolved)} numeric claims\n")
for raw, how, src in seen:
    print(f"  OK  {raw:>10}  [{how}]  {src}")

if unresolved:
    print(f"\nFAIL -- {len(unresolved)} number(s) resolve to nothing:")
    for raw in sorted(set(unresolved)):
        print(f"  {raw!r} is in the writeup and in no source. Recompute it, or add it to "
              f"ALLOWLIST naming the file that owns it.")
    sys.exit(1)

print(f"\nPASS -- every one of {len(seen)} numeric claims resolves to a source.")
