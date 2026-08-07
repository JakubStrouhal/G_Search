import { supabase } from '@/config/supabase'

export interface DemandCell {
  market: string
  city: string
  concept: string
  seed_searches: number
  live_abstentions: number
  city_empty_events: number
  notify_requests: number
}

// The demand loop's aggregate view: cells where seed demand exists but the
// city stocks nothing for that concept — v_demand_by_cell recut per source,
// anti-joined against v_city_inventory (never a hand-picked "supply void"
// list). "unmet in this city" covers two different mechanisms at once
// (both are, by definition, absent from v_city_inventory for this exact
// market+city+concept): true abstain rows, where the whole MARKET stocks
// nothing (live_abstentions), and city_empty rows, where the market stocks it
// somewhere else and only this city is empty (city_empty_events, added by the
// screens_city_empty migration). Both are real merchant-acquisition signal;
// neither is summed into the other.
export async function fetchUnmetDemand(): Promise<DemandCell[]> {
  const [{ data: cells, error: cellsErr }, { data: stocked, error: stockedErr }] = await Promise.all([
    supabase
      .from('v_demand_by_cell')
      .select('market, city, concept, seed_searches, live_abstentions, city_empty_events, notify_requests'),
    supabase.from('v_city_inventory').select('market, city, concept'),
  ])
  if (cellsErr) throw new Error(cellsErr.message)
  if (stockedErr) throw new Error(stockedErr.message)

  const stockedKeys = new Set((stocked ?? []).map((r) => `${r.market}|${r.city}|${r.concept}`))
  return (cells ?? [])
    .filter((c) => !stockedKeys.has(`${c.market}|${c.city}|${c.concept}`))
    .sort((a, b) => b.seed_searches - a.seed_searches)
}

// s2p (search-to-purchase), computed live off query_classes exactly the way
// 001-part-b/SPEC.md §5 defines it: "on searches that returned results, CTR *
// click->purchase". Verified against local (2026-08-07) to reproduce Part A's
// published CTR / click-to-purchase / s2p figures before this was wired in —
// so the acquisition brief's lost-purchase line is a live computation, never
// a number typed from the SPEC's own worked example.
export async function fetchS2p(): Promise<number> {
  const { data, error } = await supabase.from('query_classes').select('searches, zeros, clicks, buys')
  if (error) throw new Error(error.message)
  let searches = 0
  let zeros = 0
  let buys = 0
  for (const row of data ?? []) {
    searches += row.searches as number
    zeros += row.zeros as number
    buys += row.buys as number
  }
  const nonZeroSearches = searches - zeros
  if (nonZeroSearches <= 0) throw new Error('No non-zero-result searches to compute s2p from.')
  return buys / nonZeroSearches
}
