import { supabase } from '@/config/supabase'

export interface MarketCity {
  market: string
  city: string
}

// The 20 market×city combos live in public.cities, not in a component — the
// selector must never hand-type a market or city (010-screens/SPEC.md, "no
// number is a literal", extended here to the same rule for a location string).
export async function fetchCities(): Promise<MarketCity[]> {
  const { data, error } = await supabase
    .from('cities')
    .select('market, city')
    .order('market')
    .order('city')
  if (error) throw new Error(error.message)
  return data ?? []
}
