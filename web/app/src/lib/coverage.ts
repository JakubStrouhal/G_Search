import { supabase } from '@/config/supabase'

// query_classes.csv loads as a table (001-part-b/SPEC.md §6) precisely so the
// coverage table stays mechanically linked to Part A rather than a copy that
// can drift. 751 rows, small enough to aggregate client-side rather than
// standing up a view for one section.

export interface CoverageRow {
  failure_class: string
  pairs: number
  searches: number
}

export async function fetchCoverageSummary(): Promise<CoverageRow[]> {
  const { data, error } = await supabase.from('query_classes').select('failure_class, searches')
  if (error) throw new Error(error.message)
  const map = new Map<string, CoverageRow>()
  for (const row of data ?? []) {
    const key = row.failure_class as string
    const entry = map.get(key) ?? { failure_class: key, pairs: 0, searches: 0 }
    entry.pairs += 1
    entry.searches += row.searches as number
    map.set(key, entry)
  }
  return [...map.values()]
}

// The "where was the answer?" cut (001-part-b/SPEC.md §3) — the four bucket
// columns already live on query_classes, summed here rather than typed.
export interface BucketSummary {
  nowhere: number
  same_city: number
  another_city: number
  cant_tell: number
  total: number
}

export async function fetchBucketSummary(): Promise<BucketSummary> {
  const { data, error } = await supabase
    .from('query_classes')
    .select('dead_nowhere, dead_same_city, dead_another_city, dead_cant_tell, deads')
  if (error) throw new Error(error.message)
  const sum: BucketSummary = { nowhere: 0, same_city: 0, another_city: 0, cant_tell: 0, total: 0 }
  for (const row of data ?? []) {
    sum.nowhere += row.dead_nowhere as number
    sum.same_city += row.dead_same_city as number
    sum.another_city += row.dead_another_city as number
    sum.cant_tell += row.dead_cant_tell as number
    sum.total += row.deads as number
  }
  return sum
}
