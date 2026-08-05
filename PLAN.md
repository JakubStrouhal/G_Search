# Groupon R29944 — decomposition and next-step plan

Written 2026-08-05. Inputs: the case-study brief PDF, `Context/search_log.csv`,
`Context/deals.csv`, the verified Part A findings in `Context/FINDINGS.md`, and a
live reconnaissance pass over groupon.co.uk / .de / .pl done today.

---

## 1. What they are claiming

The brief opens with a business framing. Not all of it is checkable with what
they gave us, and being explicit about which is which is one of the things they
say they are grading.

| Their claim | Can we test it with the supplied data? |
|---|---|
| International markets ≈ ⅓ of orders but < ¼ of revenue | **No.** No order or revenue data at all. |
| AOV outside the US ≈ 60% of US levels | **No.** No US baseline, and `purchased` is a flag with no link to which deal was bought. `price_usd` exists but cannot be joined to a purchase. |
| "Customers are finding us and buying. They are just not finding the right thing often enough." | **Partially.** We can measure dead ends precisely. We cannot measure "the right thing" — there is no relevance label and no query→deal mapping. This gap is the whole exercise. |
| Search/browse/homepage built for the US: dense supply, English queries | **Partially, and this is the most valuable untested claim.** See task 1.3. |
| Thinner inventory in international markets | **Within-dataset only.** 568 deals, 15 unique titles per market, 5 L2 categories. No US baseline to compare against. |
| "Synthetic but modelled on real patterns and real market weights" | **Partially checkable, and worth checking.** Search volume runs GB 2,587 > ES 1,997 > FR 1,772 > DE 1,724 > PL 917. DE placing fourth is surprising for a European Groupon footprint. Flag as a question about the generator, not as a finding. |

Two framing moves in the brief are worth noticing because they change what a
good answer looks like:

- **"We are deliberately not telling you what to look for."** The obvious metric
  (zero-result rate) is a trap — it is the first thing that looks like a finding.
- **"Your prototype has to handle every kind of query you found in Part A,
  including the ones you cannot fix."** They are telling you in advance that some
  of the demand is unservable, and that the honest empty state is a graded
  deliverable, not an error path.

## 2. What they gave us, and what is conspicuously missing

**Given:** `search_log.csv` (8,997 searches, June 2026, 613 unique queries,
5 markets × 4 cities) and `deals.csv` (568 live deals, 75 unique titles,
4 L1 / 5 L2 categories).

**Missing, and each absence shapes what can be concluded:**

- **Query → deal mapping.** `results_shown` is a bare count. We can never observe
  *what* was returned, only *how many*. This single omission is what makes the
  most important failure mode invisible.
- **Relevance scores / ranker output.** So "intermittent" queries cannot be
  attributed to a threshold vs. thin supply.
- **Session IDs, timestamps, reformulations.** No way to see a user retrying,
  narrowing, or giving up — the strongest behavioural signal of a bad result set.
- **Impressions and position.** No way to distinguish "not returned" from
  "returned and buried".

The brief says to state what you would ask for in production. That list above
*is* the ask, and it should appear in Part C.

## 3. What is already established (Part A, verified)

Reproduced from `validate.py` today; see `CLAUDE.md` for known drift.

- **The headline is not 29.3%.** Zero results = 29.3%, but 1–2 results (23.2%)
  converts like zero (CTR 10.3% vs 51.7% at 4+ results). There is a cliff, not a
  gradient. **The defensible number is 52.5% combined dead-end.**
- **It is not one broken country.** Market zero-rates span 26.9% (DE) to 32.6%
  (PL); only the PL/DE pair has non-overlapping Wilson CIs. Flat across all four
  weeks of June. Do not build a per-market narrative.
- **64.2% of zero-result searches are a supply void** — 185 market+query pairs
  that return zero *every single time*, overwhelmingly adrenaline/aerial. The
  `activities` category holds only city tours, escape rooms and karting. Search
  cannot fix this.
- **35.8% are intermittent**, with a median city-to-city spread of 0.199 —
  substantial, but not enough to explain all of it.
- **Typos are a red herring** — 7.5% of zeros by the widest definition, 1.9% by
  the near-miss definition, and most typos already resolve.
- **The invisible tier:** there are zero paintball, crossfit, sushi and bowling
  deals in the catalogue, yet those queries return full result pages at zero-rates
  indistinguishable from a query the catalogue actually stocks. Inferred from the
  category structure — **not observed**, because of the missing query→deal map.

## 4. Live reconnaissance — what real Groupon actually does

Done today against the production sites. **Important caveat: the live catalogue is
not the synthetic dataset.** Live GB stocks 300+ helicopter tours; the dataset says
GB helicopter tour is 100% zero. So this pass validates *mechanisms and UX*, not
supply numbers. Used that way, it converts the dataset's most important INFERRED
claim into something observed in the wild.

**How the query is built.** URL contract is `/search?query=<raw>` on `.co.uk`,
`.de` and `.pl` alike (`/szukaj` 404s on PL — the routes are not localised).
Search resolves through `POST /mobilenextapi/graphql`; the front end is a
TanStack-based PWA served off `grouponcdn.com`. Filters are price, rating,
giftable, bookable-online and location, plus sort and a map view. The German site
carries a "wie Suchergebnisse ermittelt werden" ("how search results are
determined") disclosure link — the affordance for honesty already exists.

**Finding 1 — the matcher does not require your words to match, and never says
so.** This is the dataset's invisible Tier 1, caught in the act. All counts are
the site's own bucketed labels, GB/London:

| Query | Result count | What actually came back |
|---|---|---|
| `massage` | 400+ deals | Ordinary London massages |
| `unicorn massage` | **400+ deals** | Ordinary London massages, 1.1–3.1 mi |
| `diving` | 20+ deals | Diving/watersports |
| `shark diving` | **80+ deals** | SCUBA, snorkelling, boating, a lifeguard e-course. No sharks. |
| `shark` | 10 deals | Shark blanket, kids' sleeping bag, animal socks, water gun |

The `massage` pair is the clean result: `massage` and `unicorn massage` both land
in the site's top count bucket (400+), so adding a token that matches nothing in
the catalogue **did not visibly reduce recall**, and 400+ results are presented
with full confidence. A bucketed label cannot establish that the two sets are
identical — 1,200 and 430 both render as "400+" — but it does rule out the
unmatched term constraining the result set in any material way.

**The `diving` pair does not fit a simple token-drop story, and I am not going to
pretend it does.** `shark diving` returns *more* than `diving` alone (80+ vs 20+).
Dropping a term cannot increase recall, so something else is happening — OR
semantics across both terms, or a two-token query routing to a broader category
(watersports) than the single token does. **Unresolved from the outside**, and
it matters: term-dropping and OR-expansion need different fixes and different
asks of the platform team. Resolving it needs the GraphQL request variables (see
below) or someone inside search.

What *is* solid, and is enough to carry the finding: **the system does not require
all query terms to be satisfied, and it never discloses which ones it honoured.**
That is the mechanism behind the dataset's silent-mismatch tier.

I tried to capture the actual GraphQL query variables by patching `window.fetch`
before re-running a search; the search did not route through the patched call and
nothing was captured. One attempt, abandoned — the behavioural evidence stands on
its own and the request shape is a nice-to-have.

**Finding 2 — thin sets get padded with filler.** `skydiving` in London returns
"2 deals": a COSHH online workplace-safety course, and a real skydive 141.5 miles
away in Devon — followed by a Groupon gift-card card and "That's All for Now."
This is the 1–2 result cliff, live.

**Finding 3 — the true zero state misattributes blame.** `fallschirmspringen` on
groupon.de (location Zittau) returns **0 Angebote** with the message *"Keine
Angebote verfügbar. Versuchen Sie, einen der angewendeten Filter zu entfernen"* —
telling the user to remove filters when no filters are applied. A "similar offers"
carousel sits below, but there is no intent capture, no radius widening, no
notify-me.

(An earlier draft called it inconsistent that the same session served Thai massage
results 75–79 km away but returned zero for skydiving. That was an inference, not
an observation — a finite maximum radius with no skydiving inside it produces the
same result with no inconsistency at all, and I never checked whether German
skydiving exists near Zittau. Dropped. What survives is what the screenshot shows
plainly: **the message blames filters the user has not applied.**)

**Finding 4 — a missing diacritic materially shrinks the result set.**

| Query (groupon.pl) | Results |
|---|---|
| `masaż tajski` (correct Polish) | **40+ ofert** |
| `masaz tajski` (ASCII, how people actually type) | **10+ ofert** |

These are the site's own bucketed labels, so **no ratio can be derived from them** —
"40+" could be 47 and "10+" could be 19. The honest statement is that one missing
diacritic produces a materially smaller result set for the same intent.

Two things must be closed before this goes in Part C. The location chip was not
visible in either PL screenshot, so **the two runs are not confirmed to share a
location**, and an unequal location would confound the comparison entirely. And
exact counts need the rendered cards counted to exhaustion. The PL site failed to
render past its skeleton on repeated retries today. Treat this as a strong lead,
not yet a finding.

**Finding 5 — cross-language works for cognates.** English `thai massage` on
groupon.de returns 20+ German Thai-massage merchants. So the matcher is not
monolingual; it is *lexical*, and it succeeds exactly where the words happen to
look alike.

**Synthesis:** these are one root cause. The matcher scores on lexical overlap
against short generic titles; terms it cannot satisfy do not constrain the result
set; and the user is never told which of their words survived. Dense US supply
hides this — with enough inventory, a loosely-matched result set usually contains
something acceptable anyway. Thin international supply exposes it. Note this is a
claim about *effect*, not implementation: the `shark diving` anomaly above shows
the internals are not a simple term-drop.

## 5. The decomposition

"Search is broken" is not one problem. Model each search as a cell in a grid of
**what supply actually exists** × **how the system responded**:

| | R1 returns it, ranked top | R2 returns it, buried | R3 returns nothing | R4 returns something else, silently |
|---|---|---|---|---|
| **S1** exists in this city | ok | ranking | **F5** | **F1 / F6** |
| **S2** exists in market, other city | ok-ish | ranking | **F3** | **F1** |
| **S3** exists in another market only | — | — | F3′ | **F1** |
| **S4** does not exist on Groupon | — | — | **F4** | **F1** |

**The zero-result metric only ever sees column R3.** Column R4 — a full page of
confident, wrong results — is invisible to every dashboard Groupon currently has,
and Finding 1 shows it is happening in production right now.

That yields six failure classes, each with a different owner, fix and metric:

| # | Class | Evidence | Owner | Fix | Prototype must |
|---|---|---|---|---|---|
| **F1** | Silent substitution — unmatched terms don't constrain results | Live: `unicorn massage` and `massage` both in the 400+ bucket. Data: paintball, crossfit, sushi, bowling stocked nowhere yet returning full pages | Search relevance | Query understanding + **disclosure of which terms were honoured** | Name what it could not match, before showing alternatives |
| **F2** | Lexical & morphological miss | Live: PL diacritics 40+ → 10+. Data: local-language intermittency | Search / i18n | Normalisation, synonyms, multilingual embeddings | Match `masaz`≡`masaż`; show it did |
| **F3** | Geographic thinness | Data: median city spread 0.199; corr(deals, zero-rate) = −0.379, n=20 | Ranking / UX | Explicit radius widening with distance framing | Offer "20 in Kraków, 90 min away" as a *choice* |
| **F4** | Category void | Data: 64.2% of zeros; adrenaline = 47.6% of all zeros | **Merchant acquisition, not search** | Honest empty state + demand capture → acquisition feed | Say we don't have it, capture the intent, log the demand |
| **F5** | Ranking cutoff | Data: no query ever returns exactly 3; same-city intermittency | Ranking | Investigate the threshold | Degrade gracefully rather than snapping to zero |
| **F6** | Intent-type confusion | Live: `shark` → shark blankets (Goods, not experiences) | Intent classification | Separate goods from local experiences | Ask or split, don't blend |

This grid is the deliverable of Part A and the specification for Part B. It is
also the answer to the brief's second grading criterion — the prototype reflects
the analysis because **each class maps to a visibly different behaviour**.

## 6. Next steps

### Phase 1 — Finish and harden Part A (~1–2 h)

- **1.1** Fix the `CONCEPT_TO_L2` bug in `validate.py` Layer 3: adrenaline maps to
  `activities`, which exists but stocks none of the requested inventory, so the
  script prints "MATCHER FAILURE" where the truth is a supply void. Add a
  "category exists but holds nothing relevant" verdict. Re-run.
- **1.2** Shrink the `unmapped` concept bucket (currently 3,806 searches / 883
  zeros) below ~10% by adding the multilingual adrenaline terms (`paracaidismo`,
  `paseo en globo`, `vol en montgolfière`, `lot balonem`, `skoki spadochronowe`,
  `lot helikopterem`). This moves the adrenaline share *up* from 47.6%.
- **1.3 — the highest-value untested claim.** Tag every query as local-language /
  English / ambiguous, then compare zero-rate and search→purchase **within the
  same concept and market**. If English queries outperform local-language ones in
  DE/FR/ES/PL, the brief's "built for the US" thesis is confirmed with a number
  rather than repeated back at them. If they don't, that is a more interesting
  finding and should be said plainly.
  **Two confounds to design out before running it.** Adrenaline concepts are ~100%
  zero in *both* languages because of the supply void, so leaving them in swamps
  any language signal — restrict the test to concepts that actually have stock.
  And exclude GB, where English *is* the local language and the comparison is
  meaningless.
- **1.4** Attach Wilson CIs to each failure class, not just the headline.
- **1.5** Sanity-check the market volume ordering (GB > ES > FR > DE > PL) against
  the claim of "real market weights". Raise DE's fourth place as a question.
- **1.6** Write down positions on the two unresolvable items: the missing
  `results_shown = 3`, and whether paintball's healthy conversion is genuine
  substitution or a generator artifact. State that the file cannot settle either.
- **1.7** Close the two live-recon loose ends before any of §4 is quoted in Part C:
  re-run the PL diacritic pair with the **location pinned to the same city** and
  count rendered cards to exhaustion; and probe the `shark diving` > `diving`
  anomaly (try other discriminator+category pairs — `tiger yoga`, `helicopter
  pizza` — to see whether extra tokens systematically *broaden* the match). If a
  pattern holds, the correct claim is OR-expansion, not term-dropping.
  Two method notes. **Pin the location explicitly on every run** — the `diving`
  and `massage` probes were run in a second tab and read via the accessibility
  tree with no screenshot, so their location chip was never observed; a
  London-vs-elsewhere difference alone would explain `shark diving` 80+ >
  `diving` 20+ with no expansion logic involved. And **repeat each load**: two
  `unicorn massage` loads returned different merchants in positions 5–6, so
  ranking has a nondeterministic or personalised component and no card-level
  comparison is safe off a single load. That instability is a mild finding in its
  own right.

### Phase 2 — Build the query classifier (~1–2 h)

- **2.1** Assign all 613 queries to F1–F6 with deterministic rules over
  (zero-rate, city spread, concept↔L2 stock, volume).
- **2.2** Hand-audit a stratified sample of ~60 and **report the classifier's
  accuracy**. A stated error rate is worth more than a clean-looking table.
- **2.3** Emit `query_classes.csv`. This is the contract between Part A and Part B
  — the prototype reads it, so the connection between analysis and build is
  mechanical rather than asserted.

### Phase 3 — Choose the bet, and write down why (~30 min)

- **Option A — a better semantic search bar.** Rejected: it addresses F2 only,
  the *smallest* bucket, ignores the 64% supply void entirely, and is invisible to
  F1. This is the trap the brief is testing for.
- **Option B — an honest discovery layer** that classifies intent, shows what
  exists, names what doesn't, and captures the unservable demand. Handles all six
  classes with visibly different behaviour. **Recommended.**
- **Option C — a merchant-acquisition dashboard** driven by failed search demand.
  Strong on F4 and it is the intersection of Groupon's two stated priorities, but
  it is not the customer-facing discovery experience the brief asks for. Fold in
  as a secondary panel behind Option B.

### Phase 4 — Prototype (~3–5 h)

Runs against the real CSVs so every claim stays checkable. Required behaviours:

- **F1:** "We couldn't match **paintball**. Here's what we do have nearby." The
  dropped token is named. This is the differentiator — it is the one failure no
  zero-result dashboard can see, and most candidates will not have found it.
- **F4:** "There's no skydiving on Groupon in Berlin." Then capture the intent
  (notify me / register demand) and surface it as an acquisition signal. The empty
  state is the product, not an error page.
- **F2/F3:** normalise the query, and offer distance as an explicit choice rather
  than silently serving something 141 miles away.
- **Everywhere:** a "why these results" disclosure — the honest version of the
  link Groupon already ships on the German site.

Pre-test the exact list they will type: `skydiving`, `helicopter tour`,
`paintball`, `masaż tajski`, `masaz tajski`, `crossfit`, `sushi`,
`hubschrauber rundflug`, an English query in a PL context, and something
deliberately absurd.

### Phase 5 — Part C and measurement (~1–2 h)

Two pages, mapped to their four bullets. The measurement section should include:

- **Primary:** search→purchase on sessions containing a previously-failing query
  class. **Health metric:** replace "zero-result rate" with **dead-end rate**
  (0 *or* 1–2 results) — the 52.5% number, not the 29.3% one.
- **The instrumentation ask:** query→results mapping plus a relevance label.
  Without it F1 stays invisible no matter what gets built. This is the concrete
  thing to request from the platform teams who own search globally.
- **What would tell you it is *not* working** — the brief asks for this explicitly
  and it is where most writeups go thin:
  - dead-end rate falls while search→purchase stays flat → results were padded,
    not fixed;
  - disclosure raises bounce without raising return visits → honesty is being read
    as absence of inventory;
  - captured demand never converts into onboarded merchants → F4 loop is
    decorative.
- **Upper bound, labelled as such:** if all 2,633 zero-result searches converted
  at the observed 11.4%, that is ~300 purchases over 30 days across 5 markets.
  (`FINDINGS.md` says 303 off a stale 11.5%; recompute and use one number.)
  Recovered demand converts worse than organic. Presenting this as a forecast
  fails the "claims survive checking" criterion outright.
- **The log:** hours, AI tools and what they got wrong. The adrenaline→`activities`
  misclassification from Phase 1.1 is a real, specific, already-documented example
  — use that rather than a generic "I checked the output".

## 7. Traps to avoid

- Leading with **spell-correction**. It is 1.9–7.5% of zeros depending on
  definition, and most typos already resolve.
- Shipping a **pretty semantic search bar** and calling it done (Option A).
- Presenting the **303-purchase upper bound** as a forecast.
- Building a **per-market narrative** when the confidence intervals overlap.
- Stating "paintball returns escape rooms" as **observed** — it is inferred from
  the category structure. The live site supports the mechanism; the dataset does
  not record it.
- Conflating **live groupon.com behaviour with the synthetic dataset**. The live
  pass proves how the matcher fails, not what the supplied catalogue contains.
