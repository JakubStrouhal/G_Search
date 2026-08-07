import { supabase } from '@/config/supabase'

export interface CellDemand {
  seed_searches: number
  live_abstentions: number
  city_empty_events: number
  notify_requests: number
}

// v_demand_by_cell, recut per source. Keyed market x city x concept — NOT the
// same number as staff.searches, which is query_classes' market-wide pair
// count. GB London's "paintball" cell reads 55 here against 102 on the
// market-wide staff row; only this one is licensed to appear as "N searches
// for this here in June" (010-screens/SPEC.md, decision 16). Four columns,
// four different meanings, never summed: seed_searches is the June log;
// live_abstentions is the market having nothing anywhere; city_empty_events
// is the market having something and this city stocking none of it (added by
// the screens_city_empty migration, kept separate from live_abstentions on
// purpose — folding it in would mislabel a number already on screen);
// notify_requests is button presses, not people.
export async function fetchCellDemand(
  market: string,
  city: string,
  concept: string,
): Promise<CellDemand | null> {
  const { data, error } = await supabase
    .from('v_demand_by_cell')
    .select('seed_searches, live_abstentions, city_empty_events, notify_requests')
    .eq('market', market)
    .eq('city', city)
    .eq('concept', concept)
    .maybeSingle()
  if (error) throw new Error(error.message)
  return data
}

// The one write path this front end has. source='notify_me' is the only value
// the append policy still permits for an anon insert after the screens_rpc_v2
// migration flip — a forged source='live' row fails at the database, not here.
// n is always 1: notify-me counts button presses, never people (no sessions).
export async function recordNotifyMe(params: {
  market: string
  city: string
  concept: string | null
  rawQuery: string
}): Promise<void> {
  const { error } = await supabase.from('demand_events').insert({
    market: params.market,
    city: params.city,
    concept: params.concept,
    raw_query: params.rawQuery,
    source: 'notify_me',
    n: 1,
  })
  if (error) throw new Error(error.message)
}
