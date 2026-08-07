# Part B — state gallery

A static, clickable mock of the five SPEC §7 demo states. Its job is to settle the three invented
design decisions in `docs/design/DESIGN-SYSTEM.md` §8 before any schema exists.

```bash
python3 web/mock/build.py
python3 -m http.server 8788 --directory web/mock   # then open localhost:8788/states.html
```

`states.html` is **generated — do not edit it.** Edit `build.py` and rebuild. Deal titles, prices,
ratings, search counts, zero-rates and the 52.5% cliff are all read from `docs/brief/*.csv` and
`docs/analysis/outputs/query_classes.csv` at build time; the CSS is inlined from
`docs/design/outputs/tokens.css` and `docs/design/assets/prototype-theme.css`.

## What it deliberately does not do

- **Which query lands in which band is hardcoded.** That mapping is the threshold sweep, SPEC §10
  step 4, which gates real UI work and does not exist yet. The page says so in a banner.
- **No cosine scores.** The staff panel shows them as *not computed* rather than inventing numbers.
  Fabricating a score in an artifact whose argument is honesty about limits would be self-defeating.
- **Adjacency is ordered by rating, not similarity** — stated on the page, for the same reason.
- No database, no embeddings, no write path. `demand_events` is a label, not a table.

## Fixture notes

- SPEC §7 demo #1 names `masaz tajski`. **That string is not in the log** — the real rows are
  `masaż tajski` (n=35) plus n=1 typos `masażtajski` and `masaż tujski`. The mock uses
  `masażtajski`, a real search, to make the normalisation point.
- Near-empty uses `escape room` in PL/Warszawa: 48% of its 21 searches returned 1–2 results, and
  Warszawa stocks exactly two escape-room deals. Both facts are real.
- `deals.csv` has a single `price_usd` column and no "was" price, so cards show one price and no
  discount badge. Inventing a strikethrough would be fabricating a discount.
