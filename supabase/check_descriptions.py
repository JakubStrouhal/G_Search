"""Enforce D2 mechanically: no description may name a concept the catalogue
cannot back.

    python3 supabase/check_descriptions.py     # exit 1 on any violation

WHAT THIS PREVENTS, precisely. SPEC §6/D2 forbids LLM-enriching the 75 service
descriptions because enrichment that writes "outdoor adventure, adrenaline,
thrills" onto the activities deals would let skydiving clear the similarity
floor. F4 would collapse into F1 and the central finding of the analysis would
become an artifact of generated text.

D2 states that as a discipline. This script makes it a test, so the guarantee
holds regardless of who or what wrote the words.

TWO FORBIDDEN GROUPS, both DERIVED from classify.py's own CONCEPTS map rather
than typed here — a third hand-maintained copy is precisely the drift CLAUDE.md
warns about:

  ABSENT    adrenaline, bowling, lashes, paintball, sushi
            The catalogue holds nothing for these. Naming one in a description
            manufactures inventory that does not exist.

  PLAUSIBLE yoga, pilates, crossfit, dining_specific
            classify.py deliberately credits these as *plausible*, never
            *stocked* — a generic "Unlimited Classes" deal MIGHT cover yoga; the
            catalogue does not say. Writing "including yoga" would silently
            promote a judgement call to a fact and erase the uncertainty the
            analysis went out of its way to preserve. This group is the subtler
            of the two and the reason the check is worth having.

Checks are substring, case-folded, accent-sensitive as written in CONCEPTS, and
run against `description` only. `gloss_en` is review scaffolding, never embedded.
"""
import contextlib
import importlib.util
import io
import re
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTIONS = ROOT / "supabase" / "service_descriptions.yaml"

_spec = importlib.util.spec_from_file_location("cl", ROOT / "docs" / "analysis" / "classify.py")
_cl = importlib.util.module_from_spec(_spec)
with contextlib.redirect_stdout(io.StringIO()):
    _spec.loader.exec_module(_cl)

CONCEPTS, STOCK_TITLE, PLAUSIBLE = _cl.CONCEPTS, _cl.STOCK_TITLE, _cl.PLAUSIBLE

ABSENT = sorted(set(CONCEPTS) - set(STOCK_TITLE) - set(PLAUSIBLE))
FORBIDDEN = {c: CONCEPTS[c] for c in ABSENT + sorted(PLAUSIBLE)}


def fold(s):
    """Case-fold and strip accents, so `masaz` and `masaż` cannot slip past."""
    return "".join(ch for ch in unicodedata.normalize("NFKD", s.casefold())
                   if not unicodedata.combining(ch))


data = yaml.safe_load(DESCRIPTIONS.read_text())["services"]

violations = []
for row in data:
    body = fold(row["description"])
    for concept, pattern in FORBIDDEN.items():
        for term in pattern.split("|"):
            t = fold(term)
            # LEFT boundary only — these are STEMS, not whole words.
            #
            # Caught by mutation-testing this script rather than by reading it: an
            # earlier version anchored both ends, to stop "lash" matching inside
            # "splash". That also made `fallschirm` fail to match
            # "Fallschirmspringen", which is the single most important term in the
            # whole list. Anchoring only the start fixes both — a stem must begin a
            # word ("splash" is rejected) but may be continued by one
            # ("Fallschirmspringen", "quadbike", "balonem" are all caught).
            if re.search(rf"(?<![^\W\d_]){re.escape(t)}", body):
                violations.append((row["market"], row["title"], concept, term))

print(f"checked {len(data)} descriptions against {len(FORBIDDEN)} forbidden concepts")
print(f"  ABSENT    ({len(ABSENT)}): {', '.join(ABSENT)}")
print(f"  PLAUSIBLE ({len(PLAUSIBLE)}): {', '.join(sorted(PLAUSIBLE))}")

# The file is only useful if it is complete and matches the catalogue exactly.
import pandas as pd  # noqa: E402

deals = pd.read_csv(ROOT / "docs" / "brief" / "deals.csv")
expected = {(m, t) for m, t in zip(deals["market"], deals["title"])}
got = {(r["market"], r["title"]) for r in data}
missing, extra = expected - got, got - expected

ok = True
if missing or extra:
    ok = False
    print(f"\nFAIL — description set does not match the catalogue's 75 (market, title) pairs")
    for m, t in sorted(missing):
        print(f"  MISSING  {m}  {t!r}")
    for m, t in sorted(extra):
        print(f"  UNKNOWN  {m}  {t!r}")

if violations:
    ok = False
    print(f"\nFAIL — {len(violations)} description(s) name a concept the catalogue cannot back:")
    for market, title, concept, term in violations:
        group = "ABSENT" if concept in ABSENT else "PLAUSIBLE"
        print(f"  {market}  {title!r}\n       contains {term!r} -> concept {concept} [{group}]")

if ok:
    print(f"\nPASS — {len(data)}/75 present, no forbidden concept named.")
sys.exit(0 if ok else 1)
