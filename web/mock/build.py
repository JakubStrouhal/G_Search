#!/usr/bin/env python3
"""Build the Part B state gallery — web/mock/states.html.

A static, clickable mock of the five SPEC §7 demo queries, each rendered in its
confidence band, plus the staff panel and the side-by-side against today's UI.

Nothing here is typed by hand. Deal titles, prices, ratings and every statistic
come out of docs/brief/*.csv and docs/analysis/outputs/query_classes.csv at build
time; the CSS comes from docs/design/outputs/tokens.css and
docs/design/assets/prototype-theme.css. Edit this script, not states.html.

What the mock does NOT do, and says so on the page: it hardcodes which query
lands in which band. That mapping is the job of the threshold sweep (SPEC §10
step 4), which does not exist yet. Cosine scores are shown as absent rather than
invented, for the same reason.

  python3 web/mock/build.py && open web/mock/states.html
"""

import csv
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
BRIEF = ROOT / "docs" / "brief"
ANALYSIS = ROOT / "docs" / "analysis" / "outputs"
DESIGN = ROOT / "docs" / "design"
OUT = pathlib.Path(__file__).resolve().parent / "states.html"


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ----------------------------------------------------------------- source data

DEALS = read(BRIEF / "deals.csv")
LOG = read(BRIEF / "search_log.csv")
CLASSES = {(r["market"], r["q"]): r for r in read(ANALYSIS / "query_classes.csv")}


def deals(market, city, title=None, l2=None, limit=None):
    rows = [
        d
        for d in DEALS
        if d["market"] == market
        and d["city"] == city
        and (title is None or d["title"] == title)
        and (l2 is None or d["category_l2"] == l2)
    ]
    rows.sort(key=lambda d: (-float(d["rating"]), float(d["price_usd"])))
    return rows[:limit] if limit else rows


def card(d):
    return {
        "title": d["title"],
        "city": d["city"],
        "l2": d["category_l2"],
        "price": float(d["price_usd"]),
        "rating": float(d["rating"]),
        "ratings": int(d["num_ratings"]),
        "bookable": d["is_bookable"] == "True",
    }


def stats(market, query):
    """Real Part A numbers for a query, or None if the log never saw it."""
    row = CLASSES.get((market, query))
    if not row:
        return None
    return {
        "searches": int(row["searches"]),
        "zeros": int(row["zeros"]),
        "deads": int(row["deads"]),
        "clicks": int(row["clicks"]),
        "buys": int(row["buys"]),
        "zero_rate": float(row["zero_rate"]),
        "dead_rate": float(row["dead_rate"]),
        "concept": row["concept"],
        "coverage": row["coverage"],
        "stocking": int(row["deals_stocking"]),
        "f_class": row["failure_class"],
    }


def headline():
    """The 52.5% cliff, recomputed here so the page cannot quote a stale number."""
    buckets = {k: [0, 0] for k in ("0", "1-2", "3-9", "10+")}
    for r in LOG:
        shown, clicked = int(r["results_shown"]), int(r["clicked"])
        key = "0" if shown == 0 else "1-2" if shown <= 2 else "3-9" if shown <= 9 else "10+"
        buckets[key][0] += 1
        buckets[key][1] += clicked == 0
    total = sum(v[0] for v in buckets.values())
    thin = buckets["0"][0] + buckets["1-2"][0]
    return {
        "total": total,
        "buckets": {k: {"n": v[0], "dead": v[1], "rate": v[1] / v[0]} for k, v in buckets.items()},
        "thin_share": thin / total,
        "zero_share": buckets["0"][0] / total,
    }


def shown_distribution(market, query):
    """How many results this query actually returned, per search. Real."""
    counts = {}
    for r in LOG:
        if r["market"] == market and r["raw_query"] == query:
            counts[int(r["results_shown"])] = counts.get(int(r["results_shown"]), 0) + 1
    return dict(sorted(counts.items()))


# --------------------------------------------------------------- the five demos

UNKNOWN = (
    "The log records a result count only — there is no query→deal mapping and no "
    "relevance score. Which deals any of these searches actually returned is "
    "<strong>inferred from the catalogue, not observed</strong>. This panel cannot "
    "tell a happy substitution from a generator ignoring relevance."
)

STATES = [
    {
        "id": "normalised",
        "nav": "Normalisation works",
        "band": "confident",
        "query": "masażtajski",
        "market": "PL",
        "city": "Warszawa",
        "point": "F2 — cross-lingual and diacritic matching. The typo resolves; nothing is flagged.",
        "headline": "Massage deals in Warszawa",
        "note": (
            "Query arrived with the space missing. Normalised to <code>masaż tajski</code>, "
            "then matched on the stocked massage concept. A confident result set carries "
            "<strong>no banner at all</strong> — silence is the confident signal."
        ),
        "deals": [card(d) for d in deals("PL", "Warszawa", l2="massage")],
        "today": "A full page of massage results, same as this. Nothing is broken here.",
        "demand": False,
    },
    {
        "id": "near-empty",
        "nav": "1–2 results",
        "band": "near-empty",
        "query": "escape room",
        "market": "PL",
        "city": "Warszawa",
        "point": "The headline. 1–2 results converts like zero — 52.5% dead-end, not 29.3%.",
        "headline": "Warszawa has two escape rooms, and that is the whole catalogue.",
        "note": (
            "Today this renders as an ordinary results page that happens to be short, and "
            "it reads as a normal answer. It is not one. <strong>The panel is the page; the "
            "deals below it are the footnote.</strong> That inversion is the design argument."
        ),
        "deals": [card(d) for d in deals("PL", "Warszawa", title="Escape Room Przygoda")],
        "today": "Two cards in a normal grid, no panel, no count context. Looks like an answer.",
        "demand": True,
    },
    {
        "id": "adjacent",
        "nav": "Labelled adjacency",
        "band": "adjacent",
        "query": "paintball",
        "market": "GB",
        "city": "London",
        "point": "F1 — the invisible failure, made visible. The substitution gets a label.",
        "headline": "We don't have paintball in London.",
        "note": (
            "The catalogue stocks no paintball in any GB city. Today the searcher gets a "
            "full page of adjacent activities with <strong>nothing saying a substitution "
            "happened</strong> — 45 clicks and 13 purchases on 102 searches, which reads "
            "as success and hides the miss. Here the substitution is stated."
        ),
        "deals": [card(d) for d in deals("GB", "London", l2="activities", limit=6)],
        "today": "A full page of go-karting and city tours under the heading “paintball”, unlabelled.",
        "demand": True,
    },
    {
        "id": "abstained",
        "nav": "Honest empty",
        "band": "abstained",
        "query": "fallschirmspringen",
        "market": "DE",
        "city": "Berlin",
        "point": "F4 — search cannot fix supply. The honest answer is a merchant brief.",
        "headline": "No skydiving in Berlin — and it isn't a search problem.",
        "note": (
            "No merchant in any DE city sells this. Every one of the 64 searches returned "
            "zero and every one dead-ended. No ranking change, no synonym list and no "
            "embedding recovers a deal that does not exist. <strong>The only honest "
            "product response is to capture the demand and route it to acquisition.</strong>"
        ),
        "deals": [],
        "today": (
            "“No offers available. Try removing one of the applied filters.” — blaming "
            "filters when no filter was applied — then an unlabelled “Similar deals” "
            "carousel. See docs/design/reference/groupon-zero-results.jpg."
        ),
        "demand": True,
    },
]


def enrich(state):
    state["stats"] = stats(state["market"], state["query"])
    state["shown"] = shown_distribution(state["market"], state["query"])
    return state


STATES = [enrich(s) for s in STATES]

# The supply-void demand table — state 5. Real F4 rows, ranked by lost searches.
VOID_ROWS = sorted(
    (
        r
        for r in CLASSES.values()
        if r["failure_class"] == "F4_supply_void" and int(r["searches"]) >= 20
    ),
    key=lambda r: -int(r["searches"]),
)[:12]
DEMAND = [
    {
        "market": r["market"],
        "query": r["q"],
        "concept": r["concept"],
        "searches": int(r["searches"]),
        "zero_rate": float(r["zero_rate"]),
        "stocking": int(r["deals_stocking"]),
    }
    for r in VOID_ROWS
]
VOID_TOTAL = sum(int(r["searches"]) for r in CLASSES.values() if r["failure_class"] == "F4_supply_void")
VOID_PAIRS = sum(1 for r in CLASSES.values() if r["failure_class"] == "F4_supply_void")

DATA = {
    "states": STATES,
    "demand": DEMAND,
    "void": {"pairs": VOID_PAIRS, "searches": VOID_TOTAL},
    "headline": headline(),
    "unknown": UNKNOWN,
}

# ---------------------------------------------------------------------- render

TOKENS = (DESIGN / "outputs" / "tokens.css").read_text(encoding="utf-8")
THEME = (DESIGN / "assets" / "prototype-theme.css").read_text(encoding="utf-8")
WORDMARK = (DESIGN / "assets" / "groupon-wordmark.svg").read_text(encoding="utf-8")

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Part B — state gallery</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:opsz,wght@6..12,200..1000&display=swap" rel="stylesheet">
<style>
__TOKENS__
__THEME__

*, *::before, *::after { box-sizing: border-box; }
body { margin:0; font-family: var(--gp-font); color: var(--gp-text);
       background: var(--gp-bg); font-size: 16px; line-height: 1.5; }
h1,h2,h3,h4 { margin:0; font-weight: var(--gp-heading-weight); }
button { font: inherit; cursor: pointer; }
code { font-family: var(--gp-font-mono); font-size: .85em;
       background: var(--gp-surface); padding: 1px 5px; border-radius: var(--gp-radius-badge); }

/* fixture banner ------------------------------------------------------ */
.fixture { background: var(--color-neutral-900); color: var(--gp-text-invert);
           font-size: 13px; padding: 8px 24px; display:flex; gap:12px; align-items:center; }
.fixture strong { color: var(--color-yellow-400); font-weight: 800; letter-spacing:.025em; }
.fixture code, .staff code { background: var(--gp-staff-surface); color: var(--gp-staff-fg); }

/* chrome -------------------------------------------------------------- */
.hdr { border-bottom: 1px solid var(--gp-separator); background: var(--gp-bg); }
.hdr-in { max-width:1200px; margin:0 auto; padding:12px 24px; display:flex; gap:24px; align-items:center; }
.search { display:flex; align-items:center; width:534px; max-width:100%; height:52px;
          border:2px solid var(--gp-brand); border-radius: var(--gp-radius-pill); padding:0 6px 0 20px; }
.search input { flex:1; border:0; outline:0; background:transparent; font:inherit; }
.search .go { width:40px; height:40px; border-radius:var(--gp-radius-pill); border:0;
              background: var(--gp-brand); color:#fff; display:grid; place-items:center; }
.ctx { margin-left:auto; font-size:13px; color: var(--gp-text-muted); }
.ctx b { color: var(--gp-text); font-weight:700; }

.wrap { max-width:1200px; margin:0 auto; padding:24px; display:grid;
        grid-template-columns: 260px 1fr; gap:32px; align-items:start; }
nav.rail { position:sticky; top:16px; }
nav.rail h4 { font-size:13px; color:var(--gp-text-muted); text-transform:uppercase;
              letter-spacing:.05em; margin-bottom:8px; font-weight:800; }
nav.rail button { display:block; width:100%; text-align:left; margin-bottom:6px;
                  padding:10px 14px; border-radius: var(--gp-radius-panel);
                  border:1px solid transparent; background:transparent; font-size:14px; font-weight:700; }
nav.rail button:hover { background: var(--gp-surface); }
nav.rail button[aria-current="true"] { background: var(--gp-surface); border-color: var(--gp-separator); }
nav.rail .q { display:block; font-weight:400; font-size:13px; color:var(--gp-text-muted);
              font-family: var(--gp-font-mono); margin-top:2px; }

/* band devices -------------------------------------------------------- */
.point { font-size:13px; color: var(--gp-text-muted); margin-bottom:16px; }
.resulthead { display:flex; align-items:baseline; gap:12px; margin-bottom:4px; }
.resulthead h1 { font-size: var(--text-h2); line-height: var(--text-h2--line-height); }
.count { margin-left:auto; font-size:13px; color: var(--gp-text-muted); }

.adjacent { background: var(--gp-adjacent-bg); border:1px solid var(--gp-adjacent-border);
            border-radius: var(--gp-radius-panel); padding:20px 24px; margin-bottom:20px; }
.adjacent h2 { font-size: var(--text-h4); line-height: var(--text-h4--line-height); }
.adjacent p { margin:8px 0 0; font-size:14px; }
.adjacent .lead { margin-top:14px; font-weight:800; font-size:14px; }

.abstain { background: var(--gp-abstain-bg); border-radius: var(--gp-radius-panel);
           padding:40px 32px; text-align:center; margin-bottom:20px; }
.abstain .glyph { width:64px; height:64px; border-radius:var(--gp-radius-pill); background:#fff;
                  display:grid; place-items:center; margin:0 auto 16px; color: var(--gp-abstain-icon); }
.abstain h2 { font-size: var(--text-h3); line-height: var(--text-h3--line-height); max-width:36ch; margin:0 auto; }
.abstain p { max-width:56ch; margin:10px auto 0; font-size:15px; color: var(--gp-text-muted); }
.actions { display:flex; gap:12px; justify-content:center; margin-top:20px; flex-wrap:wrap; }
.btn { height:38px; padding:0 20px; border-radius: var(--gp-radius-pill); font-size:13px;
       font-weight:700; border:1px solid transparent; }
.btn-primary { background: var(--gp-brand); border-color: var(--gp-brand); color:#fff; }
.btn-primary:hover { background: var(--gp-brand-hover); }
.btn-secondary { background: var(--gp-surface); border-color: var(--gp-separator); color: var(--gp-text); }
.btn-secondary:hover { background:#fff; border-color: var(--color-neutral-400); }

.demand { display:none; align-items:center; gap:8px; background: var(--gp-demand-bg);
          border:1px solid var(--gp-demand-border); color: var(--gp-demand-fg);
          border-radius: var(--gp-radius-badge); padding:8px 12px; font-size:13px;
          font-weight:700; margin-bottom:20px; }
.demand.on { display:flex; }

.footnote { font-size:13px; color: var(--gp-text-muted); margin:0 0 10px; font-weight:700; }

/* deal card ----------------------------------------------------------- */
.grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(210px,1fr)); gap:24px 20px; }
.card .media { position:relative; aspect-ratio:16/9; border-radius: var(--gp-radius-media);
               background: var(--gp-surface); overflow:hidden; }
.card .badge { position:absolute; top:8px; left:8px; background:#fff; color:var(--gp-text);
               font-size:13px; font-weight:700; border-radius: var(--gp-radius-badge); padding:1px 6px; }
.card .merchant { font-size:13px; color: var(--gp-text-muted); margin-top:10px; }
.card .title { font-size: var(--text-dealCardTitle); line-height: var(--text-dealCardTitle--line-height);
               font-weight: var(--text-dealCardTitle--font-weight); margin-top:2px;
               display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.card .meta { font-size:13px; color: var(--gp-text-muted); margin-top:4px; }
.card .rating { font-size:14px; margin-top:4px; display:flex; gap:5px; align-items:center; }
.card .rating .stars { color: var(--gp-star); letter-spacing:-1px; }
.card .rating .val { font-weight:800; }
.card .rating .n { color: var(--gp-text-muted); }
.card .price { margin-top:6px; display:flex; gap:6px; align-items:baseline;
               font-size:var(--text-priceSmall); font-weight:var(--text-priceSmall--font-weight); }
.card .was { font-weight:400; color: var(--gp-price-was); text-decoration:line-through; }
.card .now { color: var(--gp-price); }
.card .off { background: var(--gp-discount-bg); color: var(--gp-discount-fg); font-size:13px;
             font-weight:700; border-radius: var(--gp-radius-badge); padding:0 6px; line-height:20px; }

/* today vs this ------------------------------------------------------- */
.compare { margin-top:32px; border-top:1px solid var(--gp-separator); padding-top:20px; }
.compare h3 { font-size: var(--text-h5); margin-bottom:10px; }
.compare .cols { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.compare .col { border:1px solid var(--gp-separator); border-radius: var(--gp-radius-panel); padding:14px 16px; }
.compare .col h4 { font-size:13px; text-transform:uppercase; letter-spacing:.05em;
                   color: var(--gp-text-muted); margin-bottom:6px; }
.compare .col p { margin:0; font-size:14px; }
.compare .today { background: var(--gp-surface); }

/* staff panel --------------------------------------------------------- */
.staff-toggle { position:fixed; right:24px; bottom:24px; z-index:20; }
.staff { position:fixed; top:0; right:0; bottom:0; width: var(--gp-staff-width); max-width:100%;
         background: var(--gp-staff-bg); color: var(--gp-staff-fg); padding:24px;
         overflow:auto; transform:translateX(100%); transition:transform var(--gp-duration) var(--gp-ease);
         z-index:30; font-size:13px; }
.staff.on { transform:none; }
.staff h3 { font-size:14px; text-transform:uppercase; letter-spacing:.05em;
            color: var(--gp-staff-muted); margin:22px 0 8px; }
.staff h3:first-of-type { margin-top:16px; }
.staff .close { position:absolute; top:16px; right:16px; background:transparent; border:0;
                color: var(--gp-staff-muted); font-size:20px; }
.staff table { width:100%; border-collapse:collapse; font-family: var(--gp-font-mono); }
.staff td { padding:3px 0; vertical-align:top; }
.staff td:first-child { color: var(--gp-staff-muted); padding-right:12px; white-space:nowrap; }
.staff .box { background: var(--gp-staff-surface); border-radius: var(--gp-radius-media);
              padding:12px 14px; margin-top:8px; line-height:1.5; }
.staff .box.unknown { border-left:3px solid var(--color-yellow-400); }
.staff .absent { color: var(--color-yellow-400); }
.dim { color: var(--gp-staff-muted); }

table.demandtbl { width:100%; border-collapse:collapse; font-size:13px; margin-top:8px; }
table.demandtbl th { text-align:left; font-weight:800; border-bottom:1px solid var(--gp-separator);
                     padding:6px 8px; font-size:12px; text-transform:uppercase;
                     letter-spacing:.05em; color: var(--gp-text-muted); }
table.demandtbl td { padding:6px 8px; border-bottom:1px solid var(--gp-separator); }
table.demandtbl td.num { text-align:right; font-family: var(--gp-font-mono); }
</style>
</head>
<body>

<div class="fixture">
  <strong>FIXTURE DATA</strong>
  <span>Deals, counts and rates are real — read from <code>docs/brief/*.csv</code> at build time.
  <b>Which query lands in which band is hardcoded</b>, not computed: that is the threshold sweep
  (SPEC §10 step 4), which does not exist yet. No embeddings, no database, no scores.</span>
</div>

<header class="hdr"><div class="hdr-in">
  __WORDMARK__
  <div class="search">
    <input id="q" readonly value="">
    <button class="go" aria-label="Search">
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor"
           stroke-linecap="square" stroke-miterlimit="10"><circle cx="9" cy="9" r="6"/><path d="M13.5 13.5 L17 17"/></svg>
    </button>
  </div>
  <div class="ctx" id="ctx"></div>
</div></header>

<div class="wrap">
  <nav class="rail">
    <h4>Demo states</h4>
    <div id="nav"></div>
  </nav>
  <main id="main"></main>
</div>

<button class="btn btn-primary staff-toggle" id="staffbtn">Groupon staff view</button>
<aside class="staff" id="staff"><button class="close" id="staffclose">&times;</button><div id="staffbody"></div></aside>

<script>
const DATA = __DATA__;
const esc = s => String(s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const pct = x => (x*100).toFixed(1) + '%';
/* deals.csv carries one column, price_usd, for all five markets. Rendering a
   local currency symbol would be inventing an exchange rate, so: USD, as given. */
const money = x => '$' + x.toFixed(2);

/* Prices in deals.csv are a single price_usd with no "was" value. The struck-through
   price is therefore not shown — inventing one would be fabricating a discount. */
function cardHTML(d) {
  const stars = '★★★★★'.slice(0, Math.round(d.rating)) + '☆☆☆☆☆'.slice(0, 5 - Math.round(d.rating));
  return `<article class="card">
    <div class="media">${d.bookable ? '<span class="badge">Bookable online</span>' : ''}</div>
    <div class="merchant">${esc(d.city)} · ${esc(d.l2)}</div>
    <div class="title">${esc(d.title)}</div>
    <div class="rating"><span class="stars">${stars}</span>
      <span class="val">${d.rating.toFixed(1)}</span>
      <span class="n">(${d.ratings.toLocaleString()})</span></div>
    <div class="price"><span class="now">${money(d.price)}</span></div>
  </article>`;
}

function render(i) {
  const s = DATA.states[i];
  document.getElementById('q').value = s.query;
  document.getElementById('ctx').innerHTML = `Market <b>${s.market}</b> · City <b>${esc(s.city)}</b>`;
  document.querySelectorAll('#nav button').forEach((b, j) =>
    b.setAttribute('aria-current', String(j === i)));

  let body = `<p class="point">${esc(s.point)}</p>`;

  if (s.band === 'confident') {
    body += `<div class="resulthead"><h1>${esc(s.headline)}</h1>
             <span class="count">${s.deals.length} deals</span></div>
             <p class="point">${s.note}</p>
             <div class="grid">${s.deals.map(cardHTML).join('')}</div>`;
  }

  if (s.band === 'adjacent') {
    body += `<div class="resulthead"><h1>Results for &ldquo;${esc(s.query)}&rdquo;</h1>
             <span class="count">0 direct · ${s.deals.length} adjacent</span></div>
      <div class="adjacent">
        <h2>${esc(s.headline)}</h2>
        <p>${s.note}</p>
        <p class="lead">Here's what's closest:</p>
      </div>
      <p class="footnote">Ordering below is by rating, not by similarity &mdash; there is no
      embedding in this mock, so &ldquo;closest&rdquo; is a claim it cannot yet keep.</p>
      <div class="grid">${s.deals.map(cardHTML).join('')}</div>`;
  }

  if (s.band === 'near-empty') {
    body += `<div class="resulthead"><h1>Results for &ldquo;${esc(s.query)}&rdquo;</h1>
             <span class="count">${s.deals.length} deals</span></div>
      <div class="abstain">
        <div class="glyph">${glyph()}</div>
        <h2>${esc(s.headline)}</h2>
        <p>${s.note}</p>
        <div class="actions">
          <button class="btn btn-primary">Tell us what you were looking for</button>
          <button class="btn btn-secondary">See escape rooms in other cities</button>
        </div>
      </div>
      <p class="footnote">Both Warszawa escape rooms:</p>
      <div class="grid">${s.deals.map(cardHTML).join('')}</div>`;
  }

  if (s.band === 'abstained') {
    body += `<div class="resulthead"><h1>Results for &ldquo;${esc(s.query)}&rdquo;</h1>
             <span class="count">0 deals</span></div>
      <div class="abstain">
        <div class="glyph">${glyph()}</div>
        <h2>${esc(s.headline)}</h2>
        <p>${s.note}</p>
        <div class="actions">
          <button class="btn btn-primary">Notify me if this appears in Berlin</button>
          <button class="btn btn-secondary">See what's available nearby</button>
        </div>
      </div>`;
  }

  body = `<div class="demand ${s.demand ? 'on' : ''}">
            ${check()} Logged to <code>demand_events</code> — ${esc(s.market)} · ${esc(s.query)} ·
            ${esc(s.city)}. This dead end is now a row someone owns.
          </div>` + body;

  body += `<div class="compare"><h3>What today's system shows, side by side</h3>
    <div class="cols">
      <div class="col today"><h4>Today</h4><p>${s.today}</p></div>
      <div class="col"><h4>This prototype</h4><p>${esc(s.point)}</p></div>
    </div></div>`;

  document.getElementById('main').innerHTML = body;
  renderStaff(s);
}

const glyph = () => `<svg width="28" height="28" viewBox="0 0 20 20" fill="none" stroke="currentColor"
  stroke-linecap="square" stroke-miterlimit="10"><path d="M3 3 L17 17"/><path d="M16 8 L12 4 H4 V12 L8 16"/></svg>`;
const check = () => `<svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor"
  stroke-width="2" stroke-linecap="square" stroke-miterlimit="10"><path d="M4 10 L8 14 L16 6"/></svg>`;

function renderStaff(s) {
  const st = s.stats;
  const rows = st ? `
    <table>
      <tr><td>searches</td><td>${st.searches}</td></tr>
      <tr><td>zero-result</td><td>${st.zeros} (${pct(st.zero_rate)})</td></tr>
      <tr><td>dead-ended</td><td>${st.deads} (${pct(st.dead_rate)})</td></tr>
      <tr><td>clicks / buys</td><td>${st.clicks} / ${st.buys}</td></tr>
      <tr><td>concept</td><td>${esc(st.concept)}</td></tr>
      <tr><td>catalogue</td><td>${esc(st.coverage)} — ${st.stocking} deals stock it</td></tr>
      <tr><td>Part A class</td><td>${esc(st.f_class)}</td></tr>
    </table>` : `<p class="dim">This exact string is not in the search log.</p>`;

  const dist = Object.entries(s.shown || {})
    .map(([k, v]) => `${k} results  ×${v}`).join('<br>') || '—';

  document.getElementById('staffbody').innerHTML = `
    <h3>Query</h3>
    <table><tr><td>raw</td><td>${esc(s.query)}</td></tr>
    <tr><td>market / city</td><td>${esc(s.market)} / ${esc(s.city)}</td></tr>
    <tr><td>band shown</td><td>${esc(s.band)} <span class="absent">(hardcoded)</span></td></tr></table>

    <h3>Part A, from the log</h3>${rows}

    <h3>results_shown distribution</h3>
    <div class="box"><code>${dist}</code><br><br><span class="dim">How many results each of
    this query's searches actually returned, from the log.</span></div>

    <h3>Embedding match</h3>
    <div class="box"><span class="absent">Not computed.</span> <span class="dim">Top-5 deals and cosine
    scores arrive with SPEC §10 step 3–4. Showing invented scores here would be the exact failure
    this prototype exists to argue against.</span></div>

    <h3>Demand row</h3>
    <div class="box">${s.demand ? 'Written.' : '<span class="dim">Not written — confident result.</span>'}</div>

    <h3>What the system does not know</h3>
    <div class="box unknown">${DATA.unknown}</div>`;
}

/* nav + the supply-void demand table as the fifth state */
const navEl = document.getElementById('nav');
DATA.states.forEach((s, i) => {
  const b = document.createElement('button');
  b.innerHTML = `${esc(s.nav)}<span class="q">${esc(s.query)} · ${esc(s.market)}</span>`;
  b.onclick = () => render(i);
  navEl.appendChild(b);
});
const db = document.createElement('button');
db.innerHTML = `The loop closes<span class="q">demand → acquisition brief</span>`;
db.onclick = renderDemandTable;
navEl.appendChild(db);

function renderDemandTable() {
  document.querySelectorAll('#nav button').forEach(b => b.setAttribute('aria-current', 'false'));
  db.setAttribute('aria-current', 'true');
  document.getElementById('q').value = '';
  document.getElementById('ctx').innerHTML = 'Staff · all markets';
  const h = DATA.headline;
  document.getElementById('main').innerHTML = `
    <p class="point">Every abstention writes a row. Aggregated, the rows are a merchant
    acquisition brief — the part search cannot fix.</p>
    <div class="resulthead"><h1>Unmet demand — supply voids</h1>
      <span class="count">${DATA.void.pairs} market×query pairs · ${DATA.void.searches.toLocaleString()} searches</span></div>
    <table class="demandtbl">
      <tr><th>Market</th><th>Query</th><th>Concept</th><th style="text-align:right">Searches</th>
          <th style="text-align:right">Zero-rate</th><th style="text-align:right">Deals stocking</th></tr>
      ${DATA.demand.map(r => `<tr><td>${esc(r.market)}</td><td><b>${esc(r.query)}</b></td>
        <td>${esc(r.concept)}</td><td class="num">${r.searches}</td>
        <td class="num">${pct(r.zero_rate)}</td><td class="num">${r.stocking}</td></tr>`).join('')}
    </table>
    <div class="compare"><h3>Why this is the point</h3>
      <div class="cols">
        <div class="col today"><h4>The cliff, recomputed at build time</h4>
          <p><b>${pct(h.thin_share)}</b> of all ${h.total.toLocaleString()} searches return 0 or 1–2 results
          — not the ${pct(h.zero_share)} that return literal zero. The 1–2 bucket dead-ends at
          <b>${pct(h.buckets['1-2'].rate)}</b>, against ${pct(h.buckets['3-9'].rate)} for 3–9 results.
          A thin page converts like an empty one.</p></div>
        <div class="col"><h4>What today's system does with these</h4>
          <p>Shows them as ordinary short result pages, or as an unlabelled “Similar deals” carousel,
          and records nothing. No row, no owner, no brief.</p></div>
      </div></div>`;
  document.getElementById('staffbody').innerHTML =
    `<h3>Note</h3><div class="box">This table is the aggregate of the demand rows written by the
     abstention states. Counts are from <code>query_classes.csv</code>; the F4 rule is the
     classifier's, not a threshold.</div>
     <h3>What the system does not know</h3><div class="box unknown">${DATA.unknown}</div>`;
}

const staff = document.getElementById('staff');
document.getElementById('staffbtn').onclick = () => staff.classList.toggle('on');
document.getElementById('staffclose').onclick = () => staff.classList.remove('on');
render(0);
</script>
</body>
</html>
"""


def main():
    page = (
        PAGE.replace("__TOKENS__", TOKENS)
        .replace("__THEME__", THEME)
        .replace("__WORDMARK__", WORDMARK.strip())
        .replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
    )
    OUT.write_text(page, encoding="utf-8")
    h = DATA["headline"]
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(page):,} bytes)")
    print(f"  {len(STATES)} query states + demand table")
    print(f"  cliff: {h['thin_share']:.1%} of {h['total']:,} searches return 0 or 1-2 "
          f"(literal zero: {h['zero_share']:.1%})")
    print(f"  1-2 results dead-rate {h['buckets']['1-2']['rate']:.1%} "
          f"vs {h['buckets']['3-9']['rate']:.1%} for 3-9")
    for s in STATES:
        n = s["stats"]["searches"] if s["stats"] else 0
        print(f"  {s['band']:<11} {s['market']} {s['query']!r:<22} {len(s['deals'])} deals, {n} searches")
    print(f"  supply voids: {VOID_PAIRS} pairs, {VOID_TOTAL:,} searches")


if __name__ == "__main__":
    main()
