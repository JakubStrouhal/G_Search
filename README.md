# Groupon case study R29944 — Discovery, International

Submission for **Senior Product Manager, AI (Discovery, International)**.

The brief supplies a month of search logs from five international markets and the
deal inventory those searches ran against, and deliberately declines to say what to
look for. Everything below comes out of that data or out of Groupon's live
production search — every number is traceable to a script in this repo.

## Start here

| If you want to… | Read / run |
|---|---|
| Read Part A as one page | [`explainer.html`](docs/analysis/004-data-story/outputs/explainer.html) |
| Check the analysis yourself | `python3 docs/analysis/validate.py` |
| Re-derive the **live** production numbers | `docs/analysis/live_probe.js` (below) |
| See the verified findings | `docs/analysis/FINDINGS.md` |
| See the reasoning behind it | `docs/analysis/PLAN.md` |
| See what is done, pending, and what was decided | `INDEX.md` |

### Running the analysis

```bash
# All three need only pandas + numpy, take no arguments, and run from anywhere —
# paths resolve against the script file.
python3 docs/analysis/validate.py       # Layers 0–5b: shape, zero-rates, always/intermittent
                                        # split, concept coverage, typo sizing, funnel. stdout only
python3 docs/analysis/classify.py       # F1–F6 classifier + inventory location -> outputs/
                                        # query_classes.csv, fix_list.csv, inventory_location.csv
python3 docs/analysis/language_test.py  # matched-pair language test -> outputs/language_pairs.csv
```

`validate.py` is a linear sequence of `LAYER` blocks, each printing its own counts,
so any headline number traces to a line. To read one section, slice the output
rather than editing the script:

```bash
python3 docs/analysis/validate.py | sed -n '/LAYER 3 /,/LAYER 4 /p'
```

**`live_probe.js` is not run with node.** Paste it into the DevTools console on a
`groupon.co.uk` or `groupon.pl` page, then `await probeGB()` / `await probePL()` /
`await probeSuggest()`. It replays Groupon's own persisted GraphQL query to read
exact result counts, because the UI only shows rounded buckets ("400+"), and
reasoning from those buckets produced two wrong claims in an earlier draft.

## Layout

```
docs/brief/       Exactly what Groupon supplied — the PDF, search_log.csv, deals.csv.
                  Immutable input; nothing writes back to it.
docs/analysis/    The work: FINDINGS.md (verified claims), PLAN.md (reasoning),
                  validate.py / classify.py / language_test.py / live_probe.js.
        outputs/  Generated CSVs. Regenerable, never hand-edited.
        <nnn>-*/  One folder per unit of work: BRIEF.md -> SPEC.md -> RESULT.md, or
                  CHORE.md for a maintenance unit. Working files, not deliverables.
                  Each has a README.md: what it is, how to read it, presentable or not.
docs/design/      Design tokens and the design system, shared by the app and the mock.
supabase/         Migrations, seeds, RPC — the DB and BE layer.
web/app/          Vue 3 + Vite + TS front end. web/mock/ is the static state gallery
                  that settled the design decisions — not the app.
INDEX.md          Status, queue, defects, decisions.
CLAUDE.md         Operating instructions for the AI agents used to build this.
middleware.ts     The deployment's password gate. Runs on Vercel before the CDN, on
                  every route, so the static explainer is covered too. Not run locally.
package.json      Repo root, and it holds one dependency only: @vercel/functions, for
                  middleware.ts. Vercel resolves middleware next to it. The app's own
                  package.json is web/app/package.json and is unrelated.
```

Parts A/B/C map to `docs/analysis/FINDINGS.md`, the prototype (`supabase/` +
`web/app/`), and the writeup. The numbered folders under `docs/analysis/` are
working units; `INDEX.md` states where each of the three stands.

## Deploy

```
branch → PR to main → GitHub Actions build gate → merge → Vercel builds production
                                                    ↑
                            schema is pushed by hand, before the merge
```

**What is automated.** `.github/workflows/ci.yml` runs on every PR to `main` and every
push to `main`: `npm ci` at the root (middleware's one dependency), `npm --prefix web/app ci`,
then `npm --prefix web/app run build` — the same two-part install `vercel.json` runs, so CI
cannot pass on a tree Vercel fails to build. That
build is `vue-tsc -b && vite build`, so type errors fail the gate; there is no separate
typecheck job and no test job, because there are no tests. Vercel deploys the front end
through its own Git integration — a preview per PR, production on `main`. The only
repo-side Vercel config is `vercel.json`, and it builds **from the repo root**, not from
`web/app`: `prebuild` runs `web/app/scripts/copy-explainer.mjs`, which reads
`docs/analysis/004-data-story/outputs/explainer.html` from outside the app folder. Setting
Vercel's Root Directory to `web/app` breaks that silently — leave it at the repo root.

**Password-gated.** The deployment is private: `middleware.ts` at the repo root returns **401
and a login form on every path** — the app shell, the hashed assets, and `explainer.html` alike
— until a cookie signed with the password is presented. It runs on Vercel's edge, ahead of the
CDN, which is the only place a request for a cached static file is visible at all; a gate inside
the Vue app would leave `explainer.html` served straight off the CDN beside it.

`SITE_PASSWORD` **must be set per environment** — preview and production are separate scopes, and
a variable set on one is not set on the other. It carries **no `VITE_` prefix**, deliberately:
anything `VITE_`-prefixed is inlined into the browser bundle. **With the variable unset the
deployment serves 503 on every path** and never falls through to the site — a gate that opens when
misconfigured is not a gate. Rotating the password invalidates every cookie already handed out,
because the cookie's signing key is derived from it. `npm run dev` is ungated: Vite does not run
Vercel middleware, so the gate is a property of the deployment, not of the code under it.

```bash
npx vercel env add SITE_PASSWORD preview
npx vercel env add SITE_PASSWORD production
```

**Write the passphrase down before you type it.** The Vercel CLI marks new variables **sensitive by
default on Production and Preview** (`vercel env add --no-sensitive` is the opt-out, and its own
help says that flag is what keeps the "value remains readable later"). A sensitive variable cannot
be read back — if it is lost, the only route is `vercel env update`, which rotates it and, by
design, logs everyone out.

Design and limits: `docs/analysis/009-access-gate/SPEC.md`. There is no rate limiting and no
audit trail — one shared password, so **use a four-word passphrase**; entropy is the only
brute-force control this design has.

**Not indexed.** `vercel.json` serves `X-Robots-Tag: noindex, nofollow` on every path. This is a
hiring deliverable carrying Groupon's name and a critique of Groupon's search, sitting on a
personal deployment; it should be reachable by whoever it was sent to and absent from search
results. There is deliberately **no `robots.txt` `Disallow`** — that would stop a crawler
fetching the page, so it would never read the header, and the URL can end up indexed anyway.

**What is not, and why.** Migrations. `CLAUDE.md` requires one reviewed migration generated
by `supabase db pull --local`, and explicit per-run approval before mutating SQL runs
against the remote project. An automated `supabase db push` from CI would defeat both.
So the schema goes up by hand, and it goes up **first** — merging a change that needs a
new column before the column exists ships a broken production front end.

```bash
npx supabase link --project-ref <ref>   # once; ref and DB password go in .env, never committed
npx supabase db push                    # review the diff it prints before confirming
```

**Owner-only, in the dashboards** (not doable from this repo):

| Where | What |
|---|---|
| Vercel | connect `JakubStrouhal/G_Search`; Root Directory = repo root; env `VITE_SUPABASE_URL` + `VITE_SUPABASE_PUBLISHABLE_KEY`, and `SITE_PASSWORD` **on preview and production separately** |
| Supabase | create the remote project; take the ref and the **publishable** key from its API settings |

The browser gets the publishable key only — never the legacy anon key, never the secret
key. Anything `VITE_`-prefixed is compiled into the bundle.

**Still owed.** `006-one-page/SPEC.md` §5 requires the agent's refusal fixture to run in
CI — "a refusal that stops firing is a regression". It is not wired up: there is no fixture
and no agent yet. It gets a job in `ci.yml` when build step 4 lands, and until then CI does
not cover it.

## What is broken

This section is the summary. `FINDINGS.md` owns the numbers and their caveats;
[`explainer.html`](docs/analysis/004-data-story/outputs/explainer.html) is the
readable version — one self-contained page, no kernel, with a box that replays any
of the 613 real queries.

**1. The obvious metric is the wrong one.** 29.3% of searches return zero results
— but a search returning **1–2 results converts at 1.7%**, against 16.1% at four
or more. A cliff, not a gradient. **The defensible headline is 52.5%**, and it
survives stratification within concept × city: the purchase rate moves 0.02pp and
the direction holds in 137 of 138 strata on CTR.

**2. One question sorts the failures, and the answer names the owner.** For every
one of the 4,720 dead ends: *where was the answer?*

| Where the answer was | share | who fixes it |
|---|---|---|
| Nowhere in the market | **43.2%** | Merchant acquisition — not search |
| The user's own city | **32.2%** | Search |
| Another city in the market | 3.1% | Product / UX |
| Can't tell from this catalogue | 21.5% | Not attributed |

The largest bucket is not a search problem at all. **Quote the `nowhere` band
[43.2%, 64.7%], not one end** — one tier of the coverage test is a judgement call
that moves 1,016 dead ends together, and under one reading the ordering flips.
The decomposition beats a shuffled null under every reading (excess +9.8pp to
+14.0pp, z = 19.5 to 33.6). Counts and the sensitivity table: `FINDINGS.md` §5f.

**3. The strongest single result: phrasing, measured.** The brief's own thesis is
that the platform was built for English-language queries. Matched pairs — same
concept, same market, only the words change — give **81.2% dead-end in English vs
39.0% in the local language**, a 42.3pp gap across 47 of 48 pairs. Both confounds
were killed: loanwords for unstocked concepts fail at the ordinary 44.0%, and rare
*local* queries die at 53.3%, not 81%.

**4. Sizing, with the denominator attached.** Today: **723 purchases/month** across
five markets. Fixing every class we can name returns **+36/month (+5.0%)** — about
**12%** of the recoverable opportunity, against a supply-void ceiling of **+271
(+37.5%)**. Every way of tightening the search side lowers it further (7.8%, then
5.7%); the most generous figure is the one published.

**5. It is not one broken country**, and **typos are a red herring** — market
zero-rates run 26.9% (DE) to 32.6% (PL) with only that pair non-overlapping, and
typos are 1.9%–7.5% of zeros depending on definition, most already resolving.

## What production search actually does

Tested against live Groupon. **The live catalogue is not the supplied dataset** —
this shows how a real search engine fails; it validates no number in the data.

`skydiving` on `groupon.co.uk/browse/london` (2026-08-06) returns **2 deals**: an
online COSHH workplace-safety course, and a real skydive **141.5 miles away in
Devon**. For a customer in London that is nothing — but every dashboard behind it
records a successful search. The matcher matches *fragments*: `kitesurf` returns a
"Portable Bartender Barista **Kit**".

That is the whole point of the question in §2: **a result count cannot tell you
whether search worked.** The API confirms why — no relevance score, no matched-term
field, no spell-correction field, so the client cannot distinguish a genuine match
from padding. The supplied dataset's central limitation is not a weakness of the
sample; it reproduces what the platform actually exposes.

Withdrawn claims stay visible, because the brief grades whether claims survive
checking. Two from an earlier draft of this file, corrected in
`003-live-validation/RESULT.md`: "a word that matches nothing is completely inert"
(true for nonsense, false for real words — one *removed* 40 results), and a general
two-word diacritic penalty (it replicates exactly for the `masaż` family and not at
all for three other Polish pairs). Mechanisms withdrawn earlier in the live
reconnaissance are in `PLAN.md` §4.

## How to think about it

Every search is a cell in a grid of **what supply exists** × **how the system
responded**. The zero-result metric only ever sees the "returns nothing" column —
a full page of confident, wrong results is invisible to it.

Two cuts of that grid nest rather than compete. **"Where was the answer?"** (§2) is
the one to lead with: four buckets, four owners, and it decides where engineering
effort goes. **F1–F6** sits underneath as the mechanism detail — *why* each failure
happened — and the prototype's required behaviours are keyed to those classes.
`nowhere` is exactly F1 ∪ F4, asserted in code rather than claimed. F1–F6 in
`PLAN.md` §5; the buckets in `FINDINGS.md` §5f.

Two of the six class *names* are withdrawn while their populations are kept:
**F5 "ranking cutoff"** (the live probe showed Groupon returns exactly 3 routinely,
so the inference behind it was dead) and **F3 "geographic thinness"** (only 6 of
its 321 dead ends actually have the deal in another city). Both are now residuals
with no established cause — a smaller claim than the one they replaced.

## Honest limits

**The structural one:** `results_shown` is a bare count. There is no query→deal
mapping and no relevance score, so any claim about *which* deals a query returned
is inference from category structure, not observation. This is why this repo
contains a supply-side **coverage-gap** analysis and not a sizing of "how many
searches got wrong results" — the latter is not provable from this data.

**Not testable at all with what was supplied:** the revenue and AOV claims (no
order data), and "thinner inventory" in absolute terms (no US baseline).

**Data quality, checked rather than left hanging:** no search in the supplied file
returns exactly 3 results — 0, 1, 2, then a jump to 4. That looked like a ranking
cut-off and is not: live Groupon returns exactly 3 routinely (`quadbike`,
`trapeze`), so it is a generation artifact (`FINDINGS.md` §1,
`003-live-validation/RESULT.md` P4). Otherwise the file is clean — zero nulls, zero
duplicate IDs, no funnel-impossible rows.

**Still open:** the catalogue stocks zero paintball deals, yet paintball converts
about as well as a query it does stock. Users substituting happily and a generator
that did not model relevance cannot be told apart from this file, so it is logged
unresolved in `FINDINGS.md` §3 Tier 1 rather than argued either way.

## Status

**[`INDEX.md`](INDEX.md)** — the board for Parts A/B/C, the open work queue, the
known-defect list, and the last six decisions with the reasoning behind them.

Status is stated there and nowhere else, deliberately: it previously lived in four
files and had drifted to four different answers.
