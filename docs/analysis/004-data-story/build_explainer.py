"""Inline story_data.json into the explainer template.

The template carries no numbers -- it carries a single `__STORY_DATA__` token. This script is the
only thing that puts data into the page, so the page cannot drift from the notebook that produced
the data. Run the notebook first.

    .venv/bin/python docs/analysis/004-data-story/notebook.py
    python3 docs/analysis/004-data-story/build_explainer.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"

template = (HERE / "explainer.template.html").read_text()
data_path = OUT / "story_data.json"
if not data_path.exists():
    raise SystemExit("outputs/story_data.json missing -- run notebook.py first")

data = json.loads(data_path.read_text())

# The blob is injected inside a <script>, so a literal "</script>" anywhere in a string would end
# the block early. json.dumps does not escape "/" -- do it explicitly.
blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")

if template.count("__STORY_DATA__") != 1:
    raise SystemExit("template must contain exactly one __STORY_DATA__ token")

page = template.replace("__STORY_DATA__", blob)

# The page must work from file:// with no network. Guard against a stray external reference.
#
# Two literals are exempt, and only these two. Neither is ever fetched:
#   - the pinned live probe URLs quoted in chapter 2's prose, which are evidence, not resources;
#   - the SVG/XHTML XML namespace, which `createElementNS` requires verbatim. It is an identifier
#     string compared character by character, not an address -- the browser makes no request for it.
# Everything else still fails the build, which is the point of this check.
NOT_A_FETCH = ("https://www.groupon", "http://www.w3.org/2000/svg", "http://www.w3.org/1999/xhtml")
scanned = page
for exempt in NOT_A_FETCH:
    scanned = scanned.replace(exempt, "«not-a-fetch»")
for bad in ("http://", "https://", "cdn.", "<link "):
    if bad in scanned:
        raise SystemExit(f"template references something external ({bad}) -- must be self-contained")

# ---------------------------------------------------------------------------
# THE DRIFT GUARD. The page's whole claim is that no figure is hand-typed into
# it -- every number arrives through the token above. That was a convention, and
# conventions leak: six hand-typed numbers had accumulated by 2026-08-06,
# including 8,997 spelled out in words next to the generated version, and a
# withdrawn claim about live inventory that contradicted the page's own chapter 2.
#
# So it is enforced instead. Scan the PROSE region (markup between the stylesheet
# and the script) for digit runs and for spelled-out numbers, and fail the build
# on anything not explicitly allowed.
# ---------------------------------------------------------------------------
ALLOWED_NUMERIC = {
    "1", "2", "3", "4", "5", "6", "1–4",   # chapter numbers, in headings and cross-references
    "01", "02", "03", "04", "05", "06",    # the same chapter numbers, zero-padded, in the contents
                                      # list and the part map. Position in the document, not a
                                      # measurement -- the chain they number lives in the script.
    "0", "1–2", "4+", "0–2",          # the result bands, which are names rather than measurements
    "0%",                             # the "converts at 0%" floor, definitionally exact
    "29944",                          # the requisition ID in the eyebrow
}
FORBIDDEN_WORDS = ("thousand", "hundred", "ninety", "percentage point", "per cent")

prose = page.split("</style>", 1)[1].split("<script", 1)[0]
prose = re.sub(r"<[^>]+>", " ", prose)                 # drop markup
prose = re.sub(r"&[a-z]+;|&#\d+;", " ", prose)         # drop entities

# A token is a digit run plus any %/+/en-dash that is part of the figure itself.
# Trailing sentence punctuation is stripped so "0%." and "0%" are one token.
tokens = {t.rstrip(".,;:") for t in re.findall(r"\d[\d,.]*(?:[–—]\d+)?[%+]?", prose)}
stray = tokens - ALLOWED_NUMERIC
if stray:
    raise SystemExit(
        f"drift guard: {len(stray)} hand-typed number(s) in the page's prose: "
        f"{sorted(stray)}\n"
        "Every figure must come from story_data.json via an element id. Bind it in "
        "the template and compute it in notebook.py, or add it to ALLOWED_NUMERIC "
        "here with a reason."
    )
spelled = [w for w in FORBIDDEN_WORDS if w in prose.lower()]
if spelled:
    raise SystemExit(
        f"drift guard: number spelled out in words ({spelled}) -- the digit scan "
        "cannot see these, which is exactly why they are banned. Bind it instead."
    )

dest = OUT / "explainer.html"
dest.write_text(page)
print(f"wrote {dest} ({dest.stat().st_size / 1024:.0f} KB)")
print(f"  {len(data['queries'])} queries in the replay index")
print(f"  open with: open {dest}")
