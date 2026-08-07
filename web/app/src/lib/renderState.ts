import type { RenderState, SearchDealsResponse } from '@/types/search'

// 010-screens/SPEC.md, "The state contract, exhaustive and ordered", amended
// 2026-08-07 (coordinator) to add city_empty — the RPC's own precedence
// comment (screens_city_empty migration) states the same order:
//
//   unknown_query -> refusal card
//   empty (blank input) -> no state card
//   abstain -> abstain state (near_empty is impossible there — available is 0
//              by construction)
//   else city_empty=true -> city-empty state (market scored above LOW, this
//              city stocks none of it — mutually exclusive with near_empty by
//              construction, 0 vs 1-2, so the order between them never binds)
//   else near_empty=true OVERRIDES the band -> near-empty state
//   else -> the band renders
//
// One state per response, deterministically. This function is the single place
// that decision is made — every component reads its result rather than
// re-deriving it, so precedence cannot drift between the abstain/city-empty/
// near-empty boundaries and the confident/adjacent one.
export function resolveRenderState(r: SearchDealsResponse): RenderState {
  if (r.band === 'unknown_query') return 'refusal'
  if (r.band === 'empty') return 'idle'
  if (r.band === 'abstain') return 'abstain'
  if (r.city_empty) return 'city_empty'
  if (r.near_empty) return 'near_empty'
  return r.band
}
