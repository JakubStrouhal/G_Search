---
created: 2026-08-07
updated: 2026-08-07
note: The threshold sweep — separation is real (AUC 0.805, 0.934 on confident labels), 99% of the expensive error sits on known-bad labels rather than on retrieval, and a doc-composition change that looked obviously right was tested properly and rejected.
---

# 008 — threshold sweep · result

Run 2026-08-07. `001-part-b/SPEC.md` §6, §10 step 4. Script: `sweep.py`, outputs in `outputs/`.

**This was the step that could invalidate the plan. It does not.** SPEC §1's top MUST — *failure
classes behave visibly differently* — is reachable, at a stated cost.

## The answer

| population | pairs | AUC | balanced LOW | false-confident | false-abstain |
|---|---|---|---|---|---|
| all labels, `plausible` as stocked | 437 / 314 | **0.805** | 0.440 | 16.2% | 31.2% |
| all labels, `plausible` excluded | 437 / 235 | 0.844 | 0.440 | 16.2% | 23.0% |
| **confident labels only** (90.1% of search volume) | 41 / 106 | **0.934** | 0.325 | 9.8% | 12.3% |

**false-confident** = an `absent` pair scores above LOW, so the system shows results for something
the catalogue does not stock. **That is F1**, the failure this prototype exists to fix.
**false-abstain** = a `stocked` pair falls below LOW, so it says "we don't have it" when it does.
Reported separately and never blended: a single accuracy number would hide which mistake is being
made, and the entire argument of this package is that these two are not equivalent.

## The finding that changes how every number above is read

**70 of the 71 false-confident errors — 99% — sit on `thin_n` labels**, the low-confidence concept
assignments at n≤3 already recorded as `INDEX.md` known issue #8.

Look at what they actually are:

| max_sim | pair | labelled | nearest document |
|---|---|---|---|
| 0.765 | FR `sallee de sport` | absent | *Abonnement Salle de Sport* |
| 0.753 | DE `stadrundfahrt` | absent | *Stadtführung* |
| 0.748 | ES `limpieza faciaal` | absent | *Tratamiento Facial* |

**These are typos of stocked concepts, and the embedding matched them correctly.** They score as
errors because `classify.py` could not map the typo to a concept and therefore tagged the row
`absent`. The retrieval did the right thing; the ground truth is wrong.

So the headline 16.2% is **partly measuring a known defect in the label set, not the model**. On the
147 pairs where the analysis is confident about its own labels — **90.1% of all search volume** —
AUC is **0.934** and the balanced point costs 9.8% / 12.3%.

**Both are published, and the full-population number leads.** Reporting only the confident subset
would be exactly the fitting this sweep exists to prevent. But reporting only the raw number would
attribute to the model a failure that belongs to the concept map.

*Unexpected consequence worth carrying into Part C: the semantic layer repairs typos that the
hand-built concept map misses. That is an argument for the embedding approach that the analysis did
not anticipate and could not have produced on its own.*

## The shipped threshold

**LOW = 0.40.** Full population: 23.1% / 26.4% by pair, and **6.8% / 23.2% by search volume** — which
is the number users would actually experience, because the false-confident pairs are overwhelmingly
one-off typos with tiny volume.

**HIGH = 0.55, and it is a judgement, not a calibration.** `coverage` labels *stocked vs absent*,
which is exactly what LOW separates. HIGH separates "confident results" from "labelled adjacency" —
a presentation choice for which **this dataset carries no ground truth at all**. Calling it
calibrated would be a lie; it is set above the 75th percentile of `stocked` (0.652) minus a margin,
and it should be described that way in Part C.

## What the demo script does at LOW = 0.40

| query | coverage | max_sim | band | nearest |
|---|---|---|---|---|
| PL `masaż tajski` | stocked | 0.552 | show | *Zabieg Spa i Masaż* |
| GB `paintball` | absent | 0.251 | **abstain** | *Manicure & Pedicure Package* |
| DE `fallschirmspringen` | absent | 0.177 | **abstain** | *Kartbahn Rennen* |
| ES `manicura` | stocked | 0.334 | **abstain** ← disagrees with the label | *Manicura y Pedicura* |

`manicura` is a genuine false-abstain against a document literally titled *Manicura y Pedicura*.

**It does not break the demo, and the reason matters:** SPEC §2/D1 already established that the
failure class comes from `query_classes`, never from a threshold. The band only sets presentation
confidence. So `manicura` still renders as F3, and the staff panel shows the band and the Part A
class **disagreeing** — which is precisely what the staff panel is for. A disagreement made visible
is worth more than one tuned away.

## A hypothesis I formed, tested, and was wrong about

`manicura` scores **0.334** against its full document but **0.831** against its title alone. The
category strings (`Beauty & Wellness · beauty`) are identical across 15 services per market, so they
looked like pure dilution, and dropping them from D-A's document format looked obviously right.

Tested across all 751 pairs rather than the six cases that suggested it:

| document format | AUC | AUC (confident) | balanced LOW | fc | fa |
|---|---|---|---|---|---|
| **A — `title · l1 · l2 · description` (current)** | **0.805** | **0.934** | 0.440 | 16.2% | 31.2% |
| B — `title · description` | 0.793 | 0.920 | 0.485 | 18.3% | 34.7% |
| C — `title only` | 0.677 | 0.854 | 0.530 | 40.0% | 33.8% |
| D — `title · l2 · description` | 0.804 | 0.917 | 0.490 | 15.1% | 32.5% |

**The current format wins.** The category tokens carry market and category signal that more than
pays for the dilution; title-only is far worse. `manicura` is a real individual casualty, not
evidence of a systemic flaw. **D-A stands unchanged.**

Recorded because it is a clean Part C entry: six hand-picked examples pointed one way, the full
population pointed the other, and only running it on everything settled it.

## Honesty register

- **The ground truth is not clean.** It is `classify.py`'s hand-built concept map, with a known
  cross-market gap (#13) and a known typo weakness (#8). The sweep inherits both. The confident-label
  arm exists to size that, not to escape it.
- **41 absent pairs in the confident arm is a small denominator.** The 0.934 AUC is the more
  favourable reading and rests on less data; that is why the full-population number leads.
- **HIGH is uncalibrated and always will be from this dataset.**
- **Description quality is untested.** The 75 descriptions are still unreviewed (4.3). If a specific
  class demos poorly, that text is the first suspect, ahead of the model.
- **AUC answers "is there a signal", not "which threshold to ship".** The operating point is an
  editorial choice about which mistake to prefer, and it is stated as one.

## Open

| # | Item |
|---|---|
| — | LOW/HIGH need to live in a table, not a constant — the RPC step (SPEC §10.5) |
| — | Remote still lags: migration 3 unapplied, old seed, no vectors |
| — | 4.3 review of the 75 descriptions |
