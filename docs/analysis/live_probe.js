/*
 * Groupon case study R29944 — live search probe.
 *
 * Purpose: the numbers in PLAN.md §4 are claims about the PRODUCTION Groupon
 * search, not about the supplied CSVs. The brief says "we will run it or check
 * it, so show your working" — this file is how the live half gets checked.
 *
 * WHAT IT DOES
 *   Replays the site's own search call and reads the exact result count.
 *   The UI only ever shows bucketed labels ("80+", "400+", "40+ ofert"); the
 *   API returns pagination.totalCount as an integer. Reading the buckets instead
 *   of the integer produced two wrong claims in an earlier draft of PLAN.md.
 *
 * HOW TO RUN (this is the verified path)
 *   1. Open https://www.groupon.co.uk/search?query=massage and let it render.
 *   2. Open DevTools console, paste this whole file, press Enter.
 *   3. await probeGB()   -> the GB matrix
 *   For Poland: open https://www.groupon.pl/search?query=masaz, paste, then
 *      await probePL()
 *   Must be run from a page on the same origin — the call is same-origin and
 *   relies on the session cookies the browser already has.
 *
 * RESOLVED 2026-08-06 — it does NOT. A plain curl POST to
 * /mobilenextapi/graphql with a browser user-agent but no session returns
 * HTTP 403, an HTML error page carrying `gtm.event: 'service_inaccessible'`
 * and `{"type":"Error 403","country":"CZ"}`. So the endpoint is edge-protected
 * and requires a warmed, cookie-bearing browser session on the origin.
 *
 * Consequence for tooling: any headless harness (Playwright/Puppeteer) starting
 * from a FRESH context is likely to hit the same 403. If this is ever automated,
 * it must attach to a real profile (CDP connect to the user's Chrome) or use a
 * persistent context warmed by loading the search page first — not a cold
 * request. This is why the browser-driven path worked and curl does not.
 *
 * FRAGILE BITS (expect these to rot)
 *   - PERSISTED_HASH is a build artifact of Groupon's front end. When it 404s or
 *     returns PERSISTED_QUERY_NOT_FOUND, re-capture it from any search request
 *     in the Network tab and replace it below.
 *   - `division` is Groupon's location key, not a city name: 'london',
 *     'warszawa' confirmed; 'warsaw' is a DIFFERENT and near-empty division
 *     (returns 3 for masaz vs 248 for 'warszawa'). Getting this wrong silently
 *     confounds every comparison, which is exactly what happened on the first
 *     pass. Always pin it explicitly; never rely on auto-geolocation.
 *
 * Counts were stable across repeat runs; ORDERING was not (two identical calls
 * returned different merchants in positions 5-6). Card-level comparisons need
 * repeated loads. Count-level comparisons do not.
 *
 * Observed 2026-08-05.
 *
 * ---------------------------------------------------------------------------
 * SCHEMA + CONSTRAINTS, verified 2026-08-06 by dumping a full raw response.
 * Everything above this line reads only `pagination.totalCount`; the response
 * carries considerably more, and three constraints below invalidate probe
 * shapes that look reasonable.
 *
 * The response is `[{data:{browseDealFeed:{cards,facets,pagination,browseProps}}}]`.
 *
 *   pagination  {limit, offset, nextOffset, feedToken, totalCount}
 *   cards[]     {id, uuid, optionId, url, title, adId, categoryGuid, prices,
 *                options, displayOptions, merchant, promotion, cashBack,
 *                limitedSale, imageUrls, rating, badges, discountPercentage,
 *                locationsSummary, icon, flags, invalidateAt}
 *               `id` is the merchant/deal slug and is the stable join key.
 *   facets[]    13, by id: brand, categories, categories_flat, distance,
 *               locations, price, rating, amenities, category_icons, giftable,
 *               gifting_flag_sections, bookable, sort
 *   browseProps {pageName, pageType, division, breadcrumbs, categoryPath, ...}
 *
 * C1. `offset` IS SILENTLY IGNORED when feedToken is null / isFetchMore false.
 *     offset 20 and offset 400 both return page 1 (verified: same first cards,
 *     19/20 overlap with offset 0). offset 600 against totalCount 458 still
 *     returns cards. Deep paging REQUIRES echoing pagination.feedToken back
 *     with offset:nextOffset and browseParams.isFetchMore:true — that works and
 *     yields 0 overlap between consecutive pages. Use pageAll().
 *
 * C2. AN INVALID `division` DOES NOT ERROR. It silently falls back to a default
 *     scope and `browseProps.division` echoes back whatever you SENT, so the
 *     echo is NOT confirmation. Verified on .fr: division 'paris' -> 444, while
 *     'not-a-division' and 'zzzzqqq' BOTH -> 399 with an identical locations
 *     facet. A typo'd division returns a plausible, wrong, self-consistent
 *     number. This is the 'warsaw' vs 'warszawa' trap, and it is worse than the
 *     note above records: there is no error signal at all. Always run
 *     divisionControl() for a market before trusting any number from it.
 *
 * C3. `limit` is honoured up to ~200 but returns one fewer than asked
 *     (100 -> 99, 200 -> 199, 20 -> 20 with nextOffset 19). Do not infer
 *     anything from the off-by-one; just read what came back.
 *
 * Two instruments the original probe never read, both free on every call:
 *
 *   facets.locations  per-town result counts for THIS query (154 towns for
 *                     `massage` in paris). Direct measurement of geographic
 *                     spread — F3 without inference.
 *   facets.distance   CUMULATIVE distance histogram with counts. `massage` in
 *                     paris: 19 within 1km, 198 within 5km, 272 within 10km,
 *                     of 444 total. This measures how much of a result set is
 *                     actually near the user, which is the padding/filler
 *                     question (PLAN.md §4 Finding 2) made measurable.
 *
 * Cross-host: the SAME PERSISTED_HASH resolves on .co.uk, .de and .fr
 * (verified 2026-08-06). Re-check .es and .pl before a run; if it 404s,
 * re-capture per host.
 *
 * SET vs COUNT — the upgrade that matters. `xqzjw massage` = `massage` = 458
 * was only ever a COUNT equality, which is equally consistent with a different
 * set of the same size. Closed 2026-08-06 by paging BOTH queries to exhaustion
 * (pageAll, 5 pages x limit 100, division london): 460 unique ids each,
 * Jaccard 1.0000, zero ids in one and not the other. Not a top-N sample.
 *
 * Controls that make it readable:
 *   - Noise floor: `massage` vs `massage` -> Jaccard 1.0 AND identical order.
 *     Membership does not drift between identical calls.
 *   - `massage` vs `xqzjw massage` -> same ids, DIFFERENT order. So the inert
 *     token does reach the scorer and perturbs RANKING; it just cannot add,
 *     remove or filter a single document. "The word cannot change what you get,
 *     only what order you get it in" is the sharper statement of F1.
 *
 * C7. Counts drift +/-2 within a day (massage/london: 458, 458, then 460).
 *     Pin the date; never read a small delta as an effect.
 * C8. totalCount does NOT saturate — collected uniques equalled it exactly
 *     (460 = 460), so comparisons in the 400s are valid.
 * C9. limit:1 returns a valid totalCount with 1 card — histogram() is safe.
 *
 * LIVE != THE SUPPLIED CATALOGUE, and it bites here. The dataset says paintball
 * and sushi are stocked nowhere; live GB returns 12 genuine paintball deals and
 * 28 sushi deals. So neither works as an inert-token probe live, and Part C must
 * not imply Groupon lacks them. cards[].title + cards[].categoryGuid make
 * substitution content directly OBSERVABLE live, which the supplied log cannot
 * be (it records a count only).
 */

const PERSISTED_HASH =
  'b035b25dceb8a84a64c618345cc21a14897b7328506a39b2e27fc7ca4ec2f429';
const SUGGEST_HASH =
  'a74a48153100b18d9a13c3a5b9abefac869db583b834cfe0c5d653b0ee25787c';

/** Exact result count for `query` in `division`. Returns a number, or an error string. */
async function total(query, division) {
  const body = [{
    operationName: 'BrowseDealFeed',
    variables: {
      dealFeedParams: {
        limit: 9,
        division,
        locationFromUrl: false,
        filters: [{ key: 'query', subKey: null, value: { static: query } }],
        offset: 0,
        feedToken: null,
        includeLocationsCount: true,
      },
      browseParams: { pathName: '/search', isFetchMore: false },
      allLocations: false,
    },
    extensions: { persistedQuery: { version: 1, sha256Hash: PERSISTED_HASH } },
  }];

  const res = await fetch('/mobilenextapi/graphql', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  });
  const json = await res.json();
  const page = json?.[0]?.data?.browseDealFeed?.pagination;
  return page ? page.totalCount : 'ERR ' + JSON.stringify(json).slice(0, 200);
}

async function run(queries, division) {
  const out = {};
  for (const q of queries) out[q] = await total(q, division);
  console.table(out);
  return out;
}

/*
 * GB matrix. Establishes F1: a term that matches nothing is inert.
 * `xqzjw` is the control — it returns 0 standalone, so any effect it has on a
 * two-word query would have to come from query semantics rather than its own
 * matches. It has none.
 *
 * Expected (division 'london', 2026-08-05):
 *   xqzjw 0 | dinosaur 13 | unicorn 8
 *   massage 458 | xqzjw massage 458 | unicorn massage 459 | dinosaur massage 460
 *   yoga 56 | xqzjw yoga 56 | dinosaur yoga 65
 *   pizza 40 | dinosaur pizza 45
 *   diving 29 | shark 10 | shark diving 81
 *   skydiving 2 | paintball 12 | escape room 120
 *
 * Note shark diving (81) is more than double the union of its parts (39), while
 * every dinosaur pair lands BELOW the union. Multi-term retrieval is neither a
 * union nor an intersection — see PLAN.md §4 Finding 1.
 */
const probeGB = () => run([
  'xqzjw', 'dinosaur', 'unicorn',
  'massage', 'xqzjw massage', 'unicorn massage', 'dinosaur massage',
  'yoga', 'xqzjw yoga', 'dinosaur yoga',
  'pizza', 'dinosaur pizza',
  'diving', 'shark', 'shark diving',
  'skydiving', 'paintball', 'escape room',
], 'london');

/*
 * PL matrix. Establishes F2 (diacritics) and the GB/PL divergence.
 *
 * Expected (division 'warszawa', 2026-08-05):
 *   masaz 248 | xqzjw masaz 248 | dinozaur masaz 248   <- inert token, same as GB
 *   joga 7 | xqzjw joga 7
 *   masaż 272 vs masaz 248                 -> -8.8%, single token barely hurt
 *   masaż tajski 162 vs masaz tajski 95    -> -41%
 *   masaż relaksacyjny 215 vs masaz relaksacyjny 112 -> -48%
 *   tajski 28
 *
 * The divergence: masaz tajski (95) is BELOW masaz (248), i.e. adding a matching
 * term NARROWS in PL. No GB pair did that. Same platform, different query
 * semantics per market — candidate headline for Part C, needs more PL two-token
 * pairs to confirm (PLAN.md task 1.7a).
 */
const probePL = () => run([
  'masaz', 'xqzjw masaz', 'dinozaur masaz',
  'joga', 'xqzjw joga',
  'masaż', 'masaż tajski', 'masaz tajski',
  'masaż relaksacyjny', 'masaz relaksacyjny', 'tajski',
], 'warszawa');

/*
 * Autocomplete health check.
 * On 2026-08-05 this returned INTERNAL_SERVER_ERROR ("Cannot read properties of
 * undefined (reading 'logError')") for 5/5 queries on groupon.co.uk — i.e. the
 * layer where spell correction and query understanding live was returning
 * nothing at all. Single session, single day: re-run before quoting it.
 */
async function probeSuggest(queries = ['massage', 'mass', 'skydiv', 'pizza']) {
  const out = {};
  for (const q of queries) {
    const body = [{
      operationName: 'SuggestedSearchQueries',
      variables: { input: { offset: 0, limit: 10, query: q } },
      extensions: { persistedQuery: { version: 1, sha256Hash: SUGGEST_HASH } },
    }];
    const res = await fetch('/mobilenextapi/graphql', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
      credentials: 'include',
    });
    const json = await res.json();
    out[q] = json?.[0]?.errors
      ? 'ERROR: ' + json[0].errors[0].message
      : JSON.stringify(json?.[0]?.data).slice(0, 200);
  }
  console.table(out);
  return out;
}

/* =========================================================================
 * v2 — added 2026-08-06. Everything below reads the fields the original probe
 * discarded, and guards the two silent-failure modes C1/C2 above.
 * ========================================================================= */

/*
 * Division keys.
 * VERIFIED means divisionControl() was RUN and the division's count is distinct
 * from that host's fallback — not merely that some number came back. Under C2 a
 * wrong division still returns a plausible number, so "I got 184" is not evidence.
 * Note the fallback differs per host, so it must be measured per host.
 */
const DIVISIONS = {
  GB: { host: 'www.groupon.co.uk', cities: ['london'],   fallback: 431 }, // london VERIFIED 2026-08-06: 458 vs 431
  FR: { host: 'www.groupon.fr',    cities: ['paris'],    fallback: 399 }, // paris  VERIFIED 2026-08-06: 444 vs 399
  DE: { host: 'www.groupon.de',    cities: ['berlin'],   fallback: null }, // UNVERIFIED — massage=184 observed, control NOT run
  PL: { host: 'www.groupon.pl',    cities: ['warszawa'], fallback: null }, // UNVERIFIED vs fallback. Distinguished from 'warsaw' (3) only
  ES: { host: 'www.groupon.es',    cities: ['madrid'],   fallback: null }, // UNPROBED — run divisionControl first
};

const sleep = (ms = 1500) => new Promise(r => setTimeout(r, ms));

/**
 * Full probe. Returns counts, ids AND the two facets worth reading.
 * Pace: callers should await sleep() between calls. Read-only, no writes.
 */
async function feed(query, division, { limit = 20, offset = 0, feedToken = null, isFetchMore = false } = {}) {
  const body = [{
    operationName: 'BrowseDealFeed',
    variables: {
      dealFeedParams: {
        limit, division, locationFromUrl: false,
        filters: [{ key: 'query', subKey: null, value: { static: query } }],
        offset, feedToken, includeLocationsCount: true,
      },
      browseParams: { pathName: '/search', isFetchMore },
      allLocations: false,
    },
    extensions: { persistedQuery: { version: 1, sha256Hash: PERSISTED_HASH } },
  }];
  const res = await fetch('/mobilenextapi/graphql', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body), credentials: 'include',
  });
  const json = await res.json();
  const f = json?.[0]?.data?.browseDealFeed;
  if (!f) return { err: JSON.stringify(json).slice(0, 300) };
  const fx = id => f.facets.find(x => x.id === id);
  return {
    query, division, host: location.host, date: new Date().toISOString().slice(0, 10),
    total: f.pagination.totalCount,
    returned: f.cards.length,
    nextOffset: f.pagination.nextOffset,
    feedToken: f.pagination.feedToken,
    ids: f.cards.map(c => c.id),
    titles: f.cards.map(c => c.title),
    locations: (fx('locations')?.values || []).map(v => [v.value, v.count]),
    distance: (fx('distance')?.ranges || []).map(r => [r.to, r.count]),
  };
}

/**
 * C2 GUARD — run this ONCE per host before trusting any number from it.
 * Two nonsense divisions must agree with each other and DISAGREE with the real
 * one. If your real division returns the fallback number, it is not a real
 * division and every comparison built on it is confounded.
 */
async function divisionControl(division, query = 'massage') {
  const real = await feed(query, division); await sleep();
  const junk1 = await feed(query, 'not-a-division'); await sleep();
  const junk2 = await feed(query, 'zzzzqqq');
  const fallbackStable = junk1.total === junk2.total;
  const verdict = !fallbackStable ? 'INCONCLUSIVE — fallback not stable'
    : real.total === junk1.total ? 'SUSPECT — division may be invalid or coincides with fallback'
    : 'OK — division is real and distinct from fallback';
  console.table({ real: real.total, fallback: junk1.total, verdict });
  return { host: location.host, division, real: real.total, fallback: junk1.total, verdict };
}

/** Set comparison — the F1 test. Counts can match while sets differ. */
async function compare(qA, qB, division, limit = 100) {
  const a = await feed(qA, division, { limit }); await sleep();
  const b = await feed(qB, division, { limit });
  const A = new Set(a.ids), B = new Set(b.ids);
  const inter = [...A].filter(x => B.has(x));
  const out = {
    a: `${qA} = ${a.total}`, b: `${qB} = ${b.total}`,
    countsEqual: a.total === b.total,
    compared: `${A.size} vs ${B.size} ids`,
    overlap: inter.length,
    jaccard: +(inter.length / new Set([...A, ...B]).size).toFixed(3),
    sameOrder: JSON.stringify(a.ids) === JSON.stringify(b.ids),
    onlyInA: [...A].filter(x => !B.has(x)).slice(0, 10),
    onlyInB: [...B].filter(x => !A.has(x)).slice(0, 10),
  };
  console.table(out);
  return out;
}

/** C1-correct deep paging via feedToken. Use when you need ids beyond ~199. */
async function pageAll(query, division, maxPages = 5, limit = 20) {
  const ids = []; let token = null, offset = 0, total = null;
  for (let i = 0; i < maxPages; i++) {
    const r = await feed(query, division, { limit, offset, feedToken: token, isFetchMore: i > 0 });
    if (r.err || !r.ids.length) break;
    total = r.total; ids.push(...r.ids); token = r.feedToken; offset = r.nextOffset;
    if (ids.length >= total) break;
    await sleep();
  }
  return { query, division, total, collected: ids.length, unique: new Set(ids).size, ids };
}

/**
 * P4 — does live search EVER return exactly 3? This is a DISTRIBUTION question;
 * a hand-picked matrix cannot answer it. Pass a large query list, get a
 * histogram of totalCount. Report N with the result: absence of 3 across small
 * N licenses nothing.
 */
async function histogram(queries, division) {
  const counts = {}, raw = {};
  for (const q of queries) {
    const r = await feed(q, division, { limit: 1 });
    raw[q] = r.err ? 'ERR' : r.total;
    if (!r.err) counts[r.total] = (counts[r.total] || 0) + 1;
    await sleep();
  }
  const low = Object.entries(counts).filter(([k]) => +k <= 10).sort((a, b) => +a[0] - +b[0]);
  console.log(`N=${queries.length} on ${location.host}/${division}`);
  console.log('exactly 3:', counts[3] || 0, '| low-count distribution:', JSON.stringify(low));
  console.table(raw);
  return { n: queries.length, division, host: location.host, counts, raw };
}

console.log('loaded — v1: await probeGB() / probePL() / probeSuggest()');
console.log('v2: await divisionControl("london") FIRST, then feed/compare/pageAll/histogram');
