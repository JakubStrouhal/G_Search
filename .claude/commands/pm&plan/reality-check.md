---
description: Demand-side truth test on a piece of Part B — strip the jargon, name the real need, and ask what breaks if it is cut.
argument-hint: <what to test>  (a demo case, a screen, a class behaviour — e.g. the F4 empty state)
allowed-tools: Read, Grep, Glob, Bash(ls:*), Bash(python3:*)
disable-model-invocation: true
---

Reality check: $ARGUMENTS

A critique pass, like `/review`. **It changes no file.** Anything it lands becomes a `/spec` edit or
a CUT row, made by the command that owns that file.

## Who is on the other side

**The searcher.** In London, Berlin, Paris, Madrid, Kraków. Types five to fifteen characters into a
box, in whatever language comes to hand — including one that does not match the market — and decides
within a couple of seconds whether this site has anything for them. They are not evaluating a search
engine. They are deciding whether to keep looking or close the tab. They do not know the catalogue
is empty for what they want, and today the product does not tell them: `paintball` returns a median
7–9 results and **zero** of them are paintball.

**Groupon staff** — the staff-panel audience. A supply or category manager who needs to know which
city wants what that nobody stocks, and needs to trust the number before taking it to a merchant.

The two hardest moments, and the ones worth testing first:

1. **The invisible failure (F1).** The searcher got a full page of results and left satisfied that
   Groupon has nothing for them — no zero-result event, no complaint, no signal anywhere. The
   dashboard says this search succeeded.
2. **The honest dead end (F4).** `fallschirmspringen` in Berlin: 64 searches, 64 zeros, 0 deals
   anywhere. There is no good answer and there will not be one until someone signs a merchant. The
   brief grades this case explicitly: *what it does when it has no good answer tells us as much as
   what it does when it has one.*

## 1. Read what exists

`docs/analysis/001-part-b/SPEC.md` §3 (behaviour per class), §4 (coverage table), §7 (demo script),
§8 (staff panel), §9 (honesty register). Then `docs/analysis/FINDINGS.md` for the finding under it.

`web/` and `supabase/` may not be built yet. **That is not a blocker** — run the test against the
SPEC's own copy and behaviour. Wrong words are cheapest to catch before they are typed. If the code
does exist, test the code; what shipped beats what was specified.

## 2. Four questions

**What is the searcher really trying to do?** Base human need, not feature language.
- BAD: "recover from a zero-result query"
- GOOD: "find out in two seconds whether there is anything to do in Berlin this weekend that isn't a massage"

**What are they feeling at that exact moment?** Name it. Impatience, not "friction". If the
behaviour ignores that they will close the tab rather than reformulate, say why it fails.

**Supply-side BS scan.** Every place our own vocabulary leaked into shopper-facing copy — the F-class
names, "supply void", "abstention", "similarity threshold", "normalisation", "dead-end rate", "s2p",
"demand event", "adjacency". Rewrite each from the searcher's side.

> **The staff panel is exempt, and this is a distinction the check must hold.** Cosine scores,
> which band fired, which class `query_classes.csv` assigns — that language is *correct* there and
> vague language would be the defect. Jargon is a bug in the shopper's view and a feature in the
> operator's view. Do not flatten the two.

**Is the claim checkable?** Repo-specific and non-negotiable. Every number on screen must be
computed from the CSVs, not typed by hand. Re-run the script before quoting it. If the honest answer
to something the screen implies is CANNOT VERIFY, the screen must not imply it — the log carries a
result *count only*, so any statement about *which* deals a query returned is inference.

## 3. The nth-order check

The one the generic version misses, and the one this build turns on: **does the obvious fix make it
worse?** Loosening the match to drive the zero-result rate down is exactly what produces F1 — the
dashboard goes green while trust goes down. If the thing under test would look better on a metric
while being worse for the searcher, that is the finding.

## 4. The kill question

*What happens if we cut this?*

- "Nothing bad" → it fails. Propose it for the SPEC's **CUT list**, with the reason. Cutting is not
  a loss here: the CUT rows are where judgement is visible, and output per hour is graded.
- Real consequence — the searcher leaves believing the catalogue is empty, a supply gap stays
  invisible to acquisition, a graded requirement goes unmet, a claim stops being checkable → it
  passes.

## Output

```markdown
## Reality check: <what was tested>

### The real need
One sentence. Human, not feature.

### The real emotion
One sentence, at the exact moment of use.

### Supply-side BS found
| What we say | What the searcher hears | What it should say |
|---|---|---|

### Spec vs. reality
Does the specified behaviour serve the need or our own capability? Cite `SPEC.md` sections and, if
built, files.

### Checkability
Any number or implied claim that is not computed, or that the honesty register says we cannot know.

### Nth-order
Does the obvious fix make this worse?

### Kill question
Pass / fail, with the consequence named.

### Verdict: STRONG / NEEDS WORK / RETHINK
One paragraph.
```

Report in at most 12 lines beyond the block. No file edits, no `INDEX.md` row — hand the verdict to
`/spec` if it changes the build.
