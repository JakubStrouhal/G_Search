# Groupon design system — brief for a design agent

**Audience:** an AI design/build agent producing UI for the Part B prototype in this repo.
**Goal:** the prototype should read as *a thing Groupon could ship*, not as a generic search demo
wearing a green button.
**Extracted:** 2026-08-06, from the live `https://www.groupon.com/` US homepage and search results.

Read §0 before anything else. Then §1–§7 are the system as it exists; **§8 is the part that
matters** — the screens the prototype needs that Groupon has no published design for, and the rule
for each on whether to reuse or invent.

---

## 0. How to use this document

1. **Tokens are generated, not typed.** `outputs/tokens.css` and `outputs/tokens.json` come out of
   `extract_tokens.py`. Import the CSS; do not retype hex values into components. If a number here
   and a number in `outputs/` disagree, `outputs/` wins — re-run the script.
2. **Every claim carries a tag.** This repo grades whether claims survive checking, so:
   - **[V]** *Verified* — read out of the shipped CSS or measured from computed styles on the live
     page. Reproducible by re-running the script or re-opening the page.
   - **[O]** *Observed* — read off a screenshot in `reference/`. Real, but eyeballed, not measured.
   - **[I]** *Invented* — does not exist on groupon.com. Designed here for the prototype, in
     Groupon's idiom. **Anything tagged [I] is a design decision this project is accountable for**,
     not something to attribute to Groupon.
3. **Light mode only.** groupon.com ships no dark theme [V — no `prefers-color-scheme` or
   `.dark` variant in the token layer]. Do not invent one.
4. **Do not redesign Groupon.** Where a Groupon pattern exists, match it. Divergence should be
   visible and deliberate, because every divergence in this prototype is an argument about search
   behaviour — not a taste preference.

### Method, so it can be checked

```bash
python3 docs/design/extract_tokens.py            # fetch live, regenerate outputs/
python3 docs/design/extract_tokens.py page.html  # or parse a saved copy
python3 docs/design/contrast_check.py            # regenerate the §2 contrast table
```

Groupon serves Tailwind v4 with its whole token layer inlined in a `<style>` block on the
server-rendered homepage. The script reads custom properties from **unscoped `:root` / `:host`
rules only** and converts `oklch()` / `lab()` sources to sRGB hex. 329 tokens, 178 of them colours.

Two traps it handles, both of which produce a wrong design system if ignored:

- The page also carries a `[data-templateId="livingsocial"]` block that re-points
  `--color-primary` at **blue**. A naive "last declaration wins" scrape makes the LivingSocial skin
  look like Groupon's brand colour. Groupon's primary is green; 25 theme-scoped declarations are
  excluded and reported by the script. [V]
- Chrome reports computed colours in `lab()`, and canvas `fillStyle` will not normalise those to
  hex. Hex values here are sRGB conversions of the shipped sources — exact to rounding, not
  necessarily byte-identical to what Groupon's designers typed. [V]

---

## 1. Brand

| | |
|---|---|
| Wordmark | `assets/groupon-wordmark.svg` — inline SVG lifted from the live header, 133×22 viewBox, single path set |
| Wordmark colour | **`#007C1F`**, hardcoded as a `fill` attribute on the paths [V] |
| Favicon | `assets/groupon-favicon.ico` — 64×64 and 32×32, 32-bit |
| Typeface | Nunito Sans (variable, 200–1000) + DM Serif Display for display/marketing [V] |

**Note the discrepancy and keep it.** The wordmark's `#007C1F` is *not* the primary token
(`#017c1f`). One digit apart, visually identical, and it tells you the logo predates the token
layer and was never migrated. Use the SVG as-is; use `--color-primary` for everything else. Do not
"fix" the logo to match. [V]

The logo is a Groupon trademark. It is used here because this repo *is* a Groupon case-study
deliverable. Do not put it on anything that reads as a real Groupon product surface, and do not
redistribute the assets outside this deliverable.

---

## 2. Colour

Full set: `outputs/tokens.css`. Palette ramps run 50→900 with a bare base alias
(`--color-green` = `--color-green-600`). All [V].

### The ramps

| Ramp | 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 |
|---|---|---|---|---|---|---|---|---|---|---|
| **green** (= primary) | `#e5f3e9` | `#cce8d3` | `#99d0a7` | `#66b97a` | `#33a14e` | `#008a22` | **`#017c1f`** | `#006e1b` | `#006118` | `#005314` |
| **neutral** | `#edeff2` | `#dee2e8` | `#c0c5cf` | `#9ea3ae` | `#8a8e98` | `#70747d` | `#585d68` | `#414652` | `#292f3d` | `#111827` |
| **blue** | `#e5f1fb` | `#cce4f7` | `#99c9f0` | `#66ade8` | `#3392e1` | `#0077d9` | `#006bc3` | `#005fae` | `#005398` | `#004782` |
| **purple** | `#f5edfc` | `#ecdcf8` | `#d8b9f2` | `#c596eb` | `#b173e5` | `#9e50de` | `#8e48c8` | `#7e40b2` | `#6f389b` | `#5f3085` |
| **red** | `#ffeded` | `#ffdbdb` | `#ffb7b7` | `#ff9292` | `#ff6e6e` | `#ff4a4a` | `#e64343` | `#cc3b3b` | `#b33434` | `#992c2c` |
| **yellow** | `#fff5e9` | `#feecd4` | `#fed8a8` | `#fdc57d` | `#fdb152` | `#fc9e27` | `#e38e21` | `#ca7e1d` | `#b06f1b` | `#975f18` |
| **teal** | `#e2f8fc` | `#b8f3fd` | `#84e7f8` | `#56d8ee` | `#20b6d0` | `#099eb9` | `#038da6` | `#007c92` | `#006b7d` | `#005e6f` |

Also: `--color-black: #0b111e` (not pure black), `--color-white: #ffffff`, a legacy `gray` ramp
(`#f3f4f6 · #e5e7eb · #9ca3af · #4b5563 · #374151` — stock Tailwind, superseded by `neutral`; do
not use in new work), and a `specialDark` ramp (`#e7e8e9 · #dadbdd · #ccced1 · #dee2e8 · #edeff1`).

Accent one-offs: `--color-special-star: #fdb152` (rating stars), `--color-special-galaxy-black:
#230f33`, `--color-special-pink: #db09ae`, `--color-special-amber: #fc5012`,
`--color-special-magenta: #a90085`, `--color-special-light-green: #4fe81c`.

### Semantic roles — use these, not raw ramps

| Role | Token | Value |
|---|---|---|
| Primary / brand | `--color-primary` | `#017c1f` |
| Primary hover | `--background-color-primary-hover` | `#006e1b` |
| Primary subtle fill | `--background-color-primary-subtle` | `#e5f3e9` |
| Info | `--color-info` | `#006bc3` |
| Warning | `--color-warning` | `#e38e21` |
| Danger | `--color-danger` | `#cc3b3b` |
| Success | `--color-success` | `#099eb9` — *teal, not green* |
| Extra | `--color-extra` | `#7e40b2` |
| Body text | `--text-color-body` | `#111827` |
| Muted text | `--text-color-muted` | `#70747d` |
| Tertiary text | `--text-color-tertiary` | `#9ea3ae` |
| Link | `--text-color-hyperlink` | `#0077d9` |
| Promo-code price | `--text-color-extra-price` | `#6f389b` |
| Page background | `--background-color-body` | `#ffffff` |
| Surface / muted panel | `--background-color-secondary` | `#edeff2` |
| Surface, deeper | `--background-color-tertiary` | `#dee2e8` |
| Separator | `--color-separator` | `#e7e8e9` |
| Input border | `--color-input` | `#dadbdd` |
| Overlay scrim | `--background-color-overlay` | `rgba(18,18,18,.15)` |

Plus `-subtle` background and border pairs for each status: e.g. danger `#ffeded` on
`#ffb7b7`, info `#e5f1fb` on `#99c9f0`, warning `#fff5e9` on `#fed8a8`, extra `#f5edfc` on
`#d8b9f2`.

### Two rules you can read off the live page

1. **Green means commerce, not "success."** Green carries the primary CTA, the sale price and the
   discount badge. The `success` semantic is *teal*. Do not use green for a confirmation toast. [V]
2. **Purple means "conditional price."** `#6f389b` is used only for the with-promo-code price
   (`$24.65 with code TOGETHER`) — a price you do not get by default. That is a useful precedent:
   **purple already means "this number has a caveat."** [V, and see §8]

### Contrast — WCAG 2.1, generated by `contrast_check.py`

Verbatim output. The pairs below the rule are the §8 invented combinations, checked on the same
run so they are held to the same standard.

```
 17.74  AAA                       body text on white  (#111827 on #ffffff)
  5.38  AA                        primary green on white  (#017c1f on #ffffff)
  5.38  AA                        white on primary green  (#ffffff on #017c1f)
  7.74  AAA                       promo-code price on white  (#6f389b on #ffffff)
  6.07  AA                        danger text on white  (#b33434 on #ffffff)
  4.94  AA                        discount badge fg on badge bg  (#006e1b on #cce8d3)
  5.38  AA                        sale price (green-600) on white  (#017c1f on #ffffff)
  4.51  AA                        green-500 on white  (#008a22 on #ffffff)
  4.53  AA                        link on white  (#0077d9 on #ffffff)
  4.68  AA                        muted metadata on white  (#70747d on #ffffff)
  2.53  FAILS                     tertiary on white  (#9ea3ae on #ffffff)
  2.57  FAILS                     warning on white  (#e38e21 on #ffffff)
  3.18  AA large / non-text only  success/teal on white  (#099eb9 on #ffffff)
  4.89  AA                        teal-700 on white  (#007c92 on #ffffff)
──────────────────────────────────────────────────────────────────────────────
  5.64  AA                        adjacency fg on adjacency bg  (#7e40b2 on #f5edfc)
  4.44  AA large / non-text only  teal-700 on demand-row bg  (#007c92 on #e2f8fc)
  5.61  AA                        demand-row fg on its bg  (#006b7d on #e2f8fc)
 15.40  AAA                       body on muted surface  (#111827 on #edeff2)
 15.40  AAA                       staff panel body text  (#edeff2 on #111827)
  7.01  AAA                       staff panel muted text  (#9ea3ae on #111827)
```

Three consequences, all binding:

- **Tertiary `#9ea3ae` and warning `#e38e21` fail as text.** Decorative, disabled and border use
  only. The empty-state and abstention screens carry the most important copy in the product —
  never set them in either.
- `--color-success` `#099eb9` fails as text on white; use **teal-700 `#007c92`** (4.89).
- On the demand-row's own `#e2f8fc`, even teal-700 lands at 4.44 — under AA. The demand-row
  foreground is therefore **teal-800 `#006b7d`** (5.61), which is what `prototype-theme.css` sets.

---

## 3. Typography

```
Nunito Sans      — variable, weights 200–1000. Everything.
DM Serif Display — 400 only. Marketing/hero display, e.g. "Summer's Better Together".
```

Both are Google Fonts (OFL). Self-host or:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:opsz,wght@6..12,200..1000&family=DM+Serif+Display&display=swap" rel="stylesheet">
```

`--font-sans: 'Nunito Sans Variable', sans-serif` — the stack is deliberately short; Groupon relies
on a metric-matched fallback face rather than a long system stack. [V]

### Heading scale — Groupon's own, not Tailwind's

| Token | Size | Line height | Weight |
|---|---|---|---|
| `--text-h1` | 2rem / 32px | 2.375rem | 800 |
| `--text-h2` | 1.5rem / 24px | 1.8125rem | 800 |
| `--text-h3` | 1.25rem / 20px | 1.5rem | 800 |
| `--text-h4` | 1.125rem / 18px | 1.375rem | 800 |
| `--text-h5` | 1rem / 16px | 1.1875rem | 800 |
| `--text-h6` | .875rem / 14px | 1.0625rem | 800 |

**Headings are 800 (extrabold), never 700.** That single fact does more to make a page look like
Groupon than the colour palette does. Tight leading, ~1.19–1.21×. [V]

### Body scale

| Token | Size | Line height |
|---|---|---|
| `--text-xs` | .8125rem / 13px | 1.125rem |
| `--text-sm` | .875rem / 14px | 1.25rem |
| `--text-base` | 1rem / 16px | 1.5rem |
| `--text-lg` | 1.125rem / 18px | 1.556 |
| `--text-xl` → `--text-5xl` | 1.25 / 1.5 / 1.875 / 2.25 / 3rem | ratio-based |

Note `--text-xs` is **13px, not 12px** — Groupon nudged it up. Deal-card metadata lives here. [V]

Purpose-built text tokens: `--text-dealCardTitle` 1rem/1.375rem/**700**, and
`--text-smallDealCardTitle` .875rem/1.0625rem/**800**. Deal titles are the one place weight 700
appears at heading-like prominence. [V]

**Prices get their own ramp**, which tells you how central they are: `--text-price` 18px/800,
`--text-priceMedium` 16px/800, `--text-priceSmall` 14px/800, `--text-priceMini` 12px/800,
`--text-priceTiny` 10px/700. Every step is extrabold except the smallest. A price is never set in
the body scale. [V]

Weights available: 300 light · 400 normal · 500 medium · 600 semibold · 700 bold · 800 extrabold ·
900 black. Tracking: `-.025em` tight, `.025em` wide, `.05em` wider, `.1em` widest.

---

## 4. Space, radius, elevation

**Spacing base is `.25rem` (4px).** Standard 4-point scale. [V]

### Radius — read this carefully, the scale is not monotonic

| Token | Value | |
|---|---|---|
| `--radius-xxs` | .25rem / **4px** | badges, chips, small pills |
| `--radius-md` | .375rem / **6px** | |
| `--radius-xs` | .5rem / **8px** | **deal card images** |
| `--radius-lg` | .5rem / 8px | duplicate of xs |
| `--radius-sm` | .75rem / **12px** | |
| `--radius-m` / `--radius-2xl` | 1rem / 16px | cards, panels |
| `--radius-l` / `--radius-3xl` | 1.5rem / 24px | |
| `--radius-xl` | 2rem / 32px | large surfaces |
| `--radius-pill` | **999px** | buttons, chips, search field |

`md` (6px) is *smaller* than `xs` (8px), and `xl` (32px) is 4× `sm`. **Do not assume the t-shirt
sizes ascend.** Pick by the observed usage column, not by the name. [V]

Buttons and chips compute to `calc(infinity * 1px)` in the browser — that is Tailwind's
`rounded-full`. Write `999px` or `rounded-full`; never paste the computed `1.67772e+07px`. [V]

### Elevation

Groupon composes shadows from size + colour + opacity rather than shipping finished values [V]:

```
--shadow-size-sm: 0px 1px 8px -3px      --shadow-color-black: 8,14,28
--shadow-size-md: 0px 4px 28px -6px     --shadow-color-green: 0,138,34
--shadow-size-lg: 0px 12px 63px -18px   --shadow-color-blue:  0,119,217
--shadow-size-xl: 0px 27px 105px -16px  --shadow-color-red:   255,74,74
opacity: sm-black .3 · md-black .15 · lg-black .25 · xl-black .2 · sm-green .35 · sm-blue .35
```

So the standard card shadow is `0px 4px 28px -6px rgba(8,14,28,.15)`. Wide, soft, low-opacity —
never a hard 1px drop. **The homepage barely uses elevation at all**: deal cards on white have
`box-shadow: none` and rely on the 8px image radius plus whitespace. Reserve shadow for things that
genuinely float (dropdowns, the sticky header, modals). [V]

### Motion

`--ease-out: cubic-bezier(0,0,.2,1)` · `--ease-in-out: cubic-bezier(.4,0,.2,1)`. Accordions run
190ms; filter rails 300ms. Short and unfussy. [V]

### Layout

`--breakpoint-lg: 991px` (**not** 1024 — Groupon overrides Tailwind's default) and
`--breakpoint-xl: 1280px`. Content column is **exactly 1200px**, centred, measured at a 1920px
viewport. Filter rail is `w-72` (288px) with `mr-8` (32px), hidden below `lg`. [V]

---

## 5. Components measured on groupon.com

All values below are computed styles read off the live page [V] unless tagged [O].

### Buttons

| Variant | Background | Text | Border | Size |
|---|---|---|---|---|
| Primary | `#017c1f` → hover `#006e1b` | `#ffffff` | 1px `#017c1f` | h 38px, 13px/700, `rounded-full` |
| Secondary | `#edeff2` → hover `#ffffff` | `#111827` | 1px `#e7e8e9` → hover `#8a8e98` | h 32px, 12px/700, `rounded-full`, pad 0 16px |
| Outlined | transparent → hover filled | role colour → hover `#ffffff` | 1px role colour | — |
| Link | none | `#0077d9` | none | underline on hover |

Every button label is **bold (700) and 12–13px** — small text, heavy weight, generous horizontal
padding, fully rounded. There is a full `*-outlined-hover` token family (`--text-color-primary-outlined-hover`
etc.) confirming outlined variants invert to a filled state on hover.

### Header

White. The whole `<header>` measures **176px** at a 1920px viewport: promo bar, then a search row,
then the category nav. Wordmark (133×22) sits left. The search field is a `rounded-full` container,
**534×52**, holding a 48px input, with a **green outline and a green circular submit button on the
right** [O — `reference/groupon-homepage.jpg`]; the `<input>` itself is borderless and transparent,
16px/400, `line-height: 26px` [V]. Placeholder is contextual ("Search Massage"), not generic.
Category nav sits below as an icon + label row, 14px, horizontally scrollable with a chevron
affordance.

Above the header sits a dark promo bar — purple→blue gradient, white text, countdown, pill CTA,
dismiss × [O].

### Deal card

The most-repeated object on the site. Copy its proportions exactly.

```
┌─────────────────────────────┐
│ [badge]              [♡]    │  image: aspect-video, radius 8px (--radius-xs),
│        16:9 image           │  placeholder bg #edeff2
└─────────────────────────────┘
  Merchant name (443 Locations)   13–14px, muted #70747d
  Deal title, up to two lines     16px / 1.375rem / 700  (--text-dealCardTitle), #111827
  Street address        ↗ 0.8 mi  13px muted, distance right-aligned with a nav glyph
  ★★★★☆ 4.8 (10,408)              stars #fdb152; value 14px/800 #111827; count muted
  $49  $29  [-41%]                row is --text-priceSmall (14px/800), baseline-aligned, gap 4px
                                  was:  overridden to weight 400, muted #70747d, line-through
                                  now:  green-600 #017c1f at 800  (data-testid="green-price")
                                  badge: #006e1b on #cce8d3, 13px/700, h 20px, radius 4px, pad 0 6px
  $24.65 with code TOGETHER       12px/700 in extra-price #6f389b, with a muted tail
```

Class names and `data-testid`s above are lifted from the shipped markup, so the colour roles are
read rather than eyeballed. [V]

Overlay badge ("Popular Gift", "5% Cashback"): white fill, `#111827` text, 13px/700, radius 4px,
padding 0 6px, inset ring. Wishlist heart: white circle, top-right.

Card container has **no border, no shadow, no padding, no radius** — the radius lives on the image
only. Cards are separated by grid gap alone. [V]

### Chips / filter pills

`bg-secondary` `#edeff2`, `rounded-full`, 12–13px/700, ~32px tall, 1px `#e7e8e9` border, hover to
white with a `#8a8e98` border. Used for the category filter row on results. Identical to the
secondary button — **Groupon does not distinguish chips from buttons.** [V]

### Results page furniture

- Breadcrumb: `Home / Local / Illinois`, 13px, links in `#0077d9`.
- `<h1>` "Results for &quot;query&quot;" at 24px/800, with a right-aligned **`0 deals`** count in
  muted. The count is present even when zero. [V]
- Filter rail: 288px card, `Filters` heading, collapsible groups, toggle switches, `Change
  Location` as a link.
- Sort control and `Hide filters` as inline links with icons.

### Zero-results state — `reference/groupon-zero-results.jpg`

**This is the most important screenshot in this folder.** It is the artifact SPEC §8 asks for:
*what today's system shows*. For `?query=zzqqxwv` in Chicago:

- A `#edeff2` panel, centred: a struck-through-tag glyph in a white circle, then **"No offers
  available. Try removing one of the applied filters."** at 16px/700 `#111827` [V — measured], then
  a `Clear All` text link. [O for the layout, panel proportions and glyph]
- Below it, unprompted: a **`Similar deals`** heading and a carousel of ordinary deal cards. [O]
- Above it, retained: the map panel and the full filter rail, plus an `<h1>` reading `Results for
  "zzqqxwv"` with a right-aligned `0 deals`. [O]

Three things to take from it. The first two are readings of the screenshot; the third is
**inference** — the link to Part A's F1 class is interpretation, in the sense `FINDINGS.md` uses
the word, not something this screenshot proves:

1. The message **blames the filters** [O] even though no filter was applied — the URL carried a
   query and nothing else. [V — the URL is in the screenshot]
2. `Similar deals` appear **with no label saying they are substitutes and no statement of what was
   not found**. [O]
3. *Inference:* this is the same shape as the F1 silent-substitution failure in Part A — a
   substitute presented as an answer, with no marker that a substitution happened. Note the limit:
   Part A cannot observe which deals a query returned (`results_shown` is a count only), so F1 is
   itself inferred from the catalogue. This screenshot shows production UI behaving that way in the
   zero-result case; it does not prove the log's non-zero cases behave the same. There is also
   **no next action** beyond `Clear All` — no notify-me, no route by which this dead end becomes
   information for anyone. [O]

The prototype's honest empty state (§8) is a direct answer to this screen. Put them side by side.

---

## 6. Iconography

Inline SVG, 20×20 viewBox, `stroke="currentColor"`, `stroke-miterlimit: 10`,
`stroke-linecap: square`, no fill, ~1.25–1.5px effective weight. Rendered at `size-3.5` (14px) and
`size-4` (16px). Square caps and mitred joins are distinctive — most icon sets default to round.

**Use [Lucide](https://lucide.dev) with `stroke-linecap="square"` and `stroke-linejoin="miter"`** to
approximate it [I — Groupon's set is proprietary and not extracted]. Do not mix icon families.

---

## 7. Tone of voice, as observed

Sentence case, never Title Case, outside the wordmark. Prices are the loudest thing on a card.
Copy is short, declarative and second-person. Marketing headlines take DM Serif Display; the
product UI never does. Discounts are always framed as a percentage badge next to a struck price,
never as prose. [O]

---

## 8. What the prototype needs that Groupon has no design for

This is the section that decides whether the prototype reflects the analysis or is a nice search UI
bolted on beside it. The Part B spec (`docs/analysis/001-part-b/SPEC.md` §3, §7, §8) requires the
system to handle **every** query class found in Part A, *including the ones that cannot be fixed*.
Groupon's UI has designs for exactly one of those states: confident results.

| # | Surface | Groupon has it? | Rule |
|---|---|---|---|
| 1 | Search input + market/city context | Yes | **Reuse.** Pill field, green ring, green circular submit. Add a market/city selector as a secondary chip beside it. |
| 2 | Confident results grid | Yes | **Reuse the deal card verbatim.** Do not restyle. |
| 3 | Result count / `0 deals` | Yes | **Reuse**, and extend: show the count *and* the confidence band. |
| 4 | **Near-empty state (1–2 results)** | No | **Invent [I].** See below. |
| 5 | **Labelled adjacency block** | No — this is the failure | **Invent [I].** See below. |
| 6 | **Honest empty state + notify-me** | Partially, and badly | **Invent [I], answering §5's screenshot directly.** |
| 7 | **Demand-row confirmation** | No | **Invent [I].** |
| 8 | **Staff panel** | No — internal surface | **Invent [I], deliberately unbranded.** |
| 9 | Side-by-side "what today's system would have shown" | No | **Invent [I]** — the single most persuasive artifact in the demo. |

### 8.1 The design problem in one sentence

Groupon's visual language has **one confidence level**: a grid of cards, all equally certain. The
prototype's entire argument is that a result set has *degrees* of certainty, and that 1–2 results
converts like zero. **So the primary design task is inventing a visual grammar for uncertainty that
does not exist in the source system.** Everything below follows from that.

### 8.2 The uncertainty grammar [I]

Three bands, one visual device each. Use these consistently; do not introduce a fourth.

| Band | Meaning | Device |
|---|---|---|
| **Confident** | Direct matches above threshold | Plain grid. No banner, no annotation. Silence *is* the confident signal. |
| **Adjacent** | Below threshold; shown as substitutes | Grid sits inside a **labelled container** with a `#f5edfc` / `#d8b9f2` (extra-subtle) header strip stating what was searched, what was not found, and that these are alternatives. |
| **Abstained** | Nothing worth showing | **No grid at all.** A single centred panel with the honest statement and a forward action. |

Purple carries "adjacent" because purple already means *"this number has a caveat"* on Groupon's
own cards (§2, `--text-color-extra-price`). It is an extension of an existing meaning, not a new
one. Never use green for adjacency: green is the confident-commerce colour, and reusing it here
would restate the exact failure the prototype exists to fix.

Never mark low confidence with red or warning yellow. Nothing has gone wrong; the catalogue simply
does not contain the thing. Red would read as an error state and would also fail contrast (§2).

### 8.3 Near-empty state — 1 or 2 results [I]

**The headline of the whole analysis. Do not render it as a short results grid.** A two-card grid
in Groupon's card style looks like a normal, if thin, page — which is precisely the illusion the
prototype is arguing against.

Render as: the abstention panel **first**, at full width, stating plainly that the catalogue holds
only N of these here — then the one or two real deals **below** it, unmodified. The panel is the
page; the results are a footnote to it. That inversion is the design argument.

### 8.4 Labelled adjacency [I]

Header strip above the grid, `--background-color-extra-subtle` `#f5edfc`, 1px `#d8b9f2`, radius
16px, containing:

- What was searched, quoted, at `--text-h4` (18px/800).
- **"We don't have <X> in <city>."** — explicit, in body colour, not muted. This sentence is the
  entire difference from Groupon's `Similar deals` carousel.
- **"Here's what's closest:"** as the lead-in to the grid.
- A secondary action: *notify me if this appears*.

Cards inside are the standard deal card, unmodified. **The labelling does the work, not restyling
the cards.** Compare directly against `reference/groupon-zero-results.jpg`, where the same
carousel appears with none of this.

### 8.5 Honest empty state — supply void [I]

For the F4 class, where search genuinely cannot fix the problem. Structure, in order:

1. Icon — same 20×20 square-cap stroke idiom, `#9ea3ae`, in a white circle on `#edeff2`. Reuse
   Groupon's own empty-panel geometry from §5 so it feels native.
2. **"No skydiving in Berlin — and it isn't a search problem."** `--text-h3` (20px/800),
   `#111827`. Name the query and the city. Never "no results found".
3. One line of body at 16px `#70747d`: no merchant in this city currently offers it.
4. **Primary action: notify-me.** Green primary button — the only green on the screen, because it
   is the only thing here that converts.
5. Secondary: *see what is available nearby* / *browse the category*.
6. **Never** "try removing one of the applied filters" when no filter caused it. That is the
   specific dishonesty in §5's screenshot.

### 8.6 Demand-row confirmation [I]

When a dead-end writes to `demand_events`, show a quiet inline confirmation — `#e2f8fc` fill,
`#84e7f8` border, text in **teal-800 `#006b7d`**, 13px, radius 4px, one line, no modal. Teal
because this genuinely is the `success` semantic (§2); teal-800 rather than teal-700 because
teal-700 on this fill measures 4.44 and misses AA. Keep it small: the point is that the loop
closed, not to celebrate.

### 8.7 Staff panel [I]

Per SPEC §8, worth opening on every query. **Style it as an internal tool, not as Groupon.** Dark
surface `--background-color-dark` `#111827`, `--text-color-light` `#edeff2`, monospace
(`--font-mono`) for scores and thresholds, 13px. Slide-over from the right, 420px, above the page.

Two rules:

- The **"what today's system would have shown"** comparison lives here and must use the *real,
  unmodified* Groupon deal card on the left against the prototype's treatment on the right. The
  contrast only lands if the left-hand side is visually authentic.
- The **"what the system does not know"** block must be visually equal in weight to the scores —
  same size, same colour, not a footnote. The log records a result count only, with no query→deal
  mapping, so substitution is inferred rather than observed. The brief grades honesty about limits;
  the design should not bury it in 11px grey.

---

## 9. Constraints, gaps and things not to invent

- **No dark mode exists.** Light only. [V]
- **The extracted system is US/English.** The prototype covers GB, DE, FR, ES and PL. Groupon's own
  layout is not stress-tested here for that, so: allow deal titles **three** lines, not two; test
  German compounds (`Fallschirmspringen`) at the narrowest card width; verify Polish diacritics
  (`ą ę ł ń ś ź ż`) render in Nunito Sans — they do, but the metric-matched fallback should be
  checked before relying on it.
- **Mobile is out of extraction scope.** Desktop viewport 1568px only. Breakpoints are known [V];
  mobile component behaviour is not.
- **Icons are not extracted** — the set is proprietary. Lucide is a substitution, tagged [I].
- **Hex values are sRGB conversions** of the shipped `oklch()`/hex sources, exact to rounding.
- **Do not invent Groupon brand assets.** No alternate logo lockups, no app-store badges, no
  fabricated merchant photography or reviews. Placeholder imagery must be visibly placeholder —
  `#edeff2` blocks are what Groupon itself renders while loading.
- The site is A/B tested and re-skinned continuously. `--color-special-magenta` differed between
  two fetches minutes apart (`#a40082` vs `#a60083`). Treat single-token drift as noise; re-run the
  script if precision matters.

---

## 10. Files

```
docs/design/
├── DESIGN-SYSTEM.md              this document
├── extract_tokens.py             regenerates outputs/ from the live site
├── contrast_check.py             WCAG ratios for §2, read from tokens.json
├── outputs/
│   ├── tokens.css                :root block, hex, ready to import   ← generated
│   └── tokens.json               raw + resolved + hex per token      ← generated
├── assets/
│   ├── groupon-wordmark.svg      133×22, paths filled #007C1F
│   ├── groupon-favicon.ico       64×64 + 32×32
│   └── prototype-theme.css       curated subset + the [I] tokens from §8
└── reference/
    ├── groupon-homepage.jpg      header, nav, deal-card grid
    └── groupon-zero-results.jpg  the zero-result state — see §5
```

Wire-up for the Vue prototype:

```css
@import './tokens.css';          /* generated — never hand-edit */
@import './prototype-theme.css'; /* curated + invented */
```

---

## 11. Checklist for the design agent

- [ ] Nunito Sans loaded; headings at **800**, not 700
- [ ] Deal card copied proportionally: 16:9 image, 8px radius, no card border or shadow
- [ ] Buttons `rounded-full`, bold, 12–13px
- [ ] Green used **only** for primary CTA, sale price and discount badge
- [ ] Purple `#6f389b` / `#f5edfc` used **only** for adjacency and caveated prices
- [ ] Teal, not green, for confirmations
- [ ] Every result set carries exactly one of the three confidence bands (§8.2)
- [ ] 1–2 results renders as an **abstention panel with results below**, not a short grid (§8.3)
- [ ] No empty state says "remove a filter" when no filter was applied
- [ ] Notify-me is the primary action on every dead end
- [ ] Staff panel is dark, monospaced and visually *not* Groupon
- [ ] "What the system does not know" is as prominent as the scores next to it
- [ ] Nothing sits on tertiary `#9ea3ae` or warning `#e38e21` as text (§2)
- [ ] German and Polish strings checked at the narrowest card width
