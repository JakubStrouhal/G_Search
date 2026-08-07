import { supabase } from '@/config/supabase'

// The five L2 categories this catalogue actually has (CLAUDE.md: "there are
// only five L2 categories"), scoped to what this city stocks — read live so
// the suppressed-alternatives branch never hand-types a category list that
// could drift from a reseed.
export async function fetchCityCategories(market: string, city: string): Promise<string[]> {
  const { data, error } = await supabase
    .from('deals')
    .select('category_l2')
    .eq('market', market)
    .eq('city', city)
  if (error) throw new Error(error.message)
  const set = new Set((data ?? []).map((row) => row.category_l2 as string))
  return [...set].sort()
}
