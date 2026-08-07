"""WRITEUP.md -> outputs/writeup.json, the block structure the /app#writeup page renders.

    python3 docs/analysis/011-writeup/build_writeup.py

WHY A GENERATOR AND NOT PROSE IN A COMPONENT. Two reasons, both structural.

  1. 010-screens/SPEC.md acceptance criterion 12 greps web/app/src/ for the
     headline figures (43.2, 64.7, 46.7, ...) and must find none. Part C is prose
     full of exactly those numbers. Keeping the text in docs/ and shipping it as
     a fixture keeps that criterion true BY CONSTRUCTION rather than by anyone
     remembering. Do not "simplify" this by inlining the copy into the .vue.

  2. One source. The markdown is what check_writeup.py verifies and what a
     reader gets from the repository; the page renders the same bytes. A second
     hand-maintained copy is the drift FINDINGS.md 9 row 12 already records.

The parser is deliberately small -- headings, paragraphs, bullet lists, pipe
tables, and inline strong/em/code. It is not a Markdown implementation and does
not need to be; if the writeup ever needs a construct this cannot express, add
it here rather than reaching for a runtime Markdown dependency in the browser.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = HERE / "WRITEUP.md"
DEST = HERE / "outputs" / "writeup.json"

# The heading that ends the two-page writeup and begins the log. The brief asks
# for "two pages maximum" AND "a short log" -- they are separate requests, so
# the log sits outside the page count and the split has to be explicit.
LOG_HEADING = "## The log"

INLINE = re.compile(r"(\*\*.+?\*\*|(?<!\*)\*[^*]+?\*(?!\*)|`[^`]+?`)", re.S)


def inline(text):
    """'a **b** `c`' -> [{t:text,v:a },{t:strong,v:b},...]. No HTML, no v-html."""
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            out.append({"t": "strong", "v": part[2:-2]})
        elif part.startswith("`") and part.endswith("`"):
            out.append({"t": "code", "v": part[1:-1]})
        elif part.startswith("*") and part.endswith("*"):
            out.append({"t": "em", "v": part[1:-1]})
        else:
            out.append({"t": "text", "v": part})
    return out


def row_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(md):
    """Markdown -> a flat list of blocks. Blank lines separate blocks."""
    blocks, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        if line.startswith("# "):
            blocks.append({"type": "h1", "spans": inline(line[2:].strip())})
            i += 1
        elif line.startswith("## "):
            blocks.append({"type": "h2", "spans": inline(line[3:].strip())})
            i += 1
        elif line.startswith("- "):
            items, = [[]]
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("  ")):
                if lines[i].startswith("- "):
                    items.append(lines[i][2:].strip())
                else:                                    # continuation of the item above
                    items[-1] += " " + lines[i].strip()
                i += 1
            blocks.append({"type": "ul", "items": [inline(t) for t in items]})
        elif line.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i])
                i += 1
            head = row_cells(rows[0])
            body = [row_cells(r) for r in rows[2:]]      # rows[1] is the |---| rule
            blocks.append({
                "type": "table",
                "head": [inline(c) for c in head],
                "rows": [[inline(c) for c in r] for r in body],
            })
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "- ", "|")):
                para.append(lines[i].strip())
                i += 1
            text = " ".join(para)
            # A whole paragraph in italics is the standfirst or an aside, not emphasis
            # inside a sentence. It gets its own type so the page can set it apart --
            # and the wrapping asterisks come off BEFORE inline parsing, or the outer
            # em swallows the paragraph and `code` inside it renders as backticks.
            if text.startswith("*") and text.endswith("*") and not text.startswith("**"):
                blocks.append({"type": "note", "spans": inline(text[1:-1])})
            else:
                blocks.append({"type": "p", "spans": inline(text)})
    return blocks


raw = SRC.read_text(encoding="utf-8")
if raw.startswith("---"):
    raw = raw.split("\n---\n", 1)[-1]

if LOG_HEADING not in raw:
    sys.exit(f"FAIL -- {SRC.name} has no {LOG_HEADING!r} heading; the writeup/log split is what "
             f"keeps the log outside the brief's two-page cap.")

body_md, log_md = raw.split(LOG_HEADING, 1)
body_words = len(re.findall(r"\S+", body_md))

payload = {
    "generated_by": "docs/analysis/011-writeup/build_writeup.py",
    "source": "docs/analysis/011-writeup/WRITEUP.md",
    "verified_by": "docs/analysis/011-writeup/check_writeup.py",
    "how": ("Generated. Edit WRITEUP.md and re-run the script -- a hand-edited fixture is a "
            "number that no longer traces to the data. The writeup blocks are the brief's "
            "two-page deliverable; the log is a separate request and is counted separately."),
    # SHA-256 of the markdown body this file was generated from, front matter excluded
    # (front matter is stamped on every edit and does not change the page).
    #
    # This is the seatbelt for the one failure mode the other two checks miss: edit the
    # markdown, run check_writeup.py, see it pass, commit -- and ship a page rendering the
    # OLD prose, silently. web/app/scripts/check-writeup-fixture.mjs re-hashes the source at
    # predev/prebuild and fails the build on a mismatch. Same job copy-explainer.mjs does for
    # Part A, and the same drift channel that produced FINDINGS.md 9 row 12.
    "source_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    "body_words": body_words,
    "writeup": parse(body_md),
    "log": parse(LOG_HEADING + log_md),
}

DEST.parent.mkdir(exist_ok=True)
DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

kinds = {}
for b in payload["writeup"] + payload["log"]:
    kinds[b["type"]] = kinds.get(b["type"], 0) + 1
print(f"wrote {DEST.relative_to(ROOT)}")
print(f"  writeup {len(payload['writeup'])} blocks, {body_words} words (the two-page deliverable)")
print(f"  log     {len(payload['log'])} blocks (separate from the page count, per the brief)")
print(f"  types   {', '.join(f'{k} x{v}' for k, v in sorted(kinds.items()))}")
