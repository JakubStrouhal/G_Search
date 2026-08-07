// Shape of public.search_deals()'s jsonb response — read off the live RPC, not
// guessed from the migration. Verified against local 2026-08-07:
//   psql -c "select jsonb_pretty(search_deals('GB','London','paintball',12));"
//
// Three distinct shapes share the `band` discriminant. `empty` and
// `unknown_query` are deliberately thin — the function returns early for both,
// before any of the scoring/staff work happens (search_rpc.sql). Everything
// else (`confident` | `adjacent` | `abstain`) shares one full shape, `near_empty`
// included, because the RPC always computes alternatives and near_empty even
// when it is about to abstain.

export type FullBand = 'confident' | 'adjacent' | 'abstain'

export interface DealResult {
  deal_id: string
  title: string
  price_usd: number
  rating: number | null
  num_ratings: number
  is_bookable: boolean
  city: string
  similarity: number
}

export interface Alternative {
  title: string
  category_l2: string
  similarity: number
  deal_count: number
}

export interface MatchedDoc {
  title: string
  doc: string
  similarity: number
}

// Every number here is `search_config` or `query_classes`, read live through the
// RPC — never a literal in a component (CLAUDE.md, SPEC "No number is a literal").
export interface StaffBlock {
  matched: MatchedDoc | null
  low: number
  high: number
  alt_floor: number
  alt_max: number | null
  model: string
  calibrated_on: string
  false_confident: number
  false_abstain: number
  // False means: this exact string was logged in the 613, but not in THIS
  // market — query_embeddings is keyed on q alone, query_classes on (market, q).
  // Part A has no verdict here; the caller must print no June figure.
  part_a_logged_here: boolean
  part_a_class: string | null
  part_a_coverage: 'stocked' | 'absent' | 'plausible' | null
  part_a_concept: string | null
  // CLAUDE.md: the classifier's concept map misfires on typo'd queries; every
  // affected row is thin_n. Exclude thin_label rows from any concept display.
  thin_label: boolean | null
  searches: number | null
  dead_ends: number | null
  band_agrees_with_part_a: boolean | null
  // The market-wide score, deliberately the same number as top-level
  // max_similarity under a name that states its scope: scored on market only,
  // never city. The contrast against `available` (what THIS city stocks) is
  // the city_empty finding — 424 of 12,260 combos, added 2026-08-07
  // (screens_city_empty migration).
  market_max_similarity: number | null
  // Task #17 (Codex, second pass): the RPC's own answer to "was a demand row
  // written for THIS response", decided once inside search_deals and never
  // re-derived from band/city_empty in a component — that re-derivation is
  // exactly the bug #15 caught (city_empty writes but scores confident/
  // adjacent, so a band-only check said "not written" a second after it was).
  // null on confident/adjacent rows that did not write; 'live' on abstain;
  // 'city_empty' on city_empty. Mirrors the top-level demand_row_written
  // boolean, which is what components should branch on — this is only for
  // the staff panel's "why" line.
  demand_source: 'live' | 'city_empty' | null
}

export interface FullSearchResult {
  band: FullBand
  query: string
  resolved_to: string | null
  normalised: boolean
  max_similarity: number | null
  results: DealResult[]
  result_count: number
  available: number
  near_empty: boolean
  // The market scored above LOW but this city stocks none of it — mutually
  // exclusive with near_empty by construction (0 vs 1-2). Its own render
  // state (010-screens/SPEC.md amendment, coordinator, 2026-08-07): panel
  // leads, no "Results for X" heading, no "isn't a search problem" line (the
  // market DOES stock this), no cross-city claim in any form (INDEX #12).
  city_empty: boolean
  alternatives: Alternative[]
  alternatives_above_floor: boolean
  staff: StaffBlock
  // Describes THIS response only, not a running total — a second click on
  // the same chip writes a second row by design (n=1 each, seeded month
  // stays untouchable). Never assert against a demand_events count; assert
  // against this field.
  demand_row_written: boolean
}

export interface RefusalResult {
  band: 'unknown_query'
  query: string
  why: string
  logged_queries: number
  // Carried explicitly on both early returns (refusal and blank) rather than
  // left to be inferred from absence, so the panel can say "not written, and
  // here is why" positively instead of defaulting an unknown shape to false.
  demand_row_written: false
}

export interface EmptyResult {
  band: 'empty'
  query: string
  demand_row_written: false
}

export type SearchDealsResponse = FullSearchResult | RefusalResult | EmptyResult

// The six states the SPEC's precedence rule resolves to (010-screens/SPEC.md
// "The state contract, exhaustive and ordered"). `idle` covers both "nothing
// searched yet" and the RPC's own `empty` band — a blank query renders nothing
// new either way.
export type RenderState =
  | 'idle'
  | 'refusal'
  | 'abstain'
  | 'city_empty'
  | 'near_empty'
  | 'adjacent'
  | 'confident'
