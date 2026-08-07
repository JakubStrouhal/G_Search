import { supabase } from '@/config/supabase'
import type { SearchDealsResponse } from '@/types/search'

export type SearchDealsOutcome =
  | { ok: true; data: SearchDealsResponse }
  | { ok: false; error: string }

// The RPC is the only source of a search result — no client-side scoring, no
// fallback list. "Failure is its own honest state" (010-screens/SPEC.md): a
// thrown fetch, a Postgres error and a null body are all folded into the same
// { ok: false } shape so the caller renders one error card rather than
// inventing three different silent behaviours.
export async function searchDeals(
  market: string,
  city: string,
  query: string,
  limit = 12,
): Promise<SearchDealsOutcome> {
  try {
    const { data, error } = await supabase.rpc('search_deals', {
      p_market: market,
      p_city: city,
      p_query: query,
      p_limit: limit,
    })
    if (error) return { ok: false, error: error.message }
    if (!data) return { ok: false, error: 'search_deals returned no data.' }
    return { ok: true, data: data as SearchDealsResponse }
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) }
  }
}
