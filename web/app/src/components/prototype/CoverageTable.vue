<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { fetchCoverageSummary, fetchBucketSummary, type CoverageRow, type BucketSummary } from '@/lib/coverage'

// 001-part-b/SPEC.md §4 — "ship this table in the prototype itself, not just
// in Part C". Pairs and searches are live sums off query_classes (never
// typed); the behaviour/demo-query/fixability text is prose from the SPEC,
// not a figure, so it is the one thing here that is static.
const PROSE: Record<string, { label: string; behaviour: string; demo: string; fixable: string }> = {
  F1_silent_substitution: {
    label: 'F1 — silent substitution',
    behaviour: 'Name the unmatched token; reframe as labelled adjacency',
    demo: 'paintball (GB)',
    fixable: 'Partly — needs term-constraining',
  },
  F2_language: {
    label: 'F2 — lexical / morphological',
    behaviour: 'Normalise; show the normalisation',
    demo: 'masaz tajski (PL)',
    fixable: 'Yes — the genuinely fixable layer',
  },
  F3_geographic: {
    label: 'F3 — uneven across cities',
    behaviour: 'Name the unevenness; no location claim; cross-city only where the row shows one',
    demo: 'manicura (ES)',
    fixable: 'Unknown — the mechanism was never shown',
  },
  F4_supply_void: {
    label: 'F4 — supply void',
    behaviour: 'Honest empty state + intent capture + acquisition feed',
    demo: 'fallschirmspringen (DE)',
    fixable: 'No — merchant acquisition',
  },
  F5_ranking: {
    label: 'F5 — unexplained residual',
    behaviour: 'Treat 1–2 results as near-empty (a result-count rule)',
    demo: '1–2 result case',
    fixable: 'Unknown — no cause established',
  },
  BASELINE_still_40pct_dead: {
    label: 'BASELINE residual',
    behaviour: 'No claim made',
    demo: '—',
    fixable: 'Unexplained — stated, not fixed',
  },
}

const ORDER = ['F1_silent_substitution', 'F2_language', 'F3_geographic', 'F4_supply_void', 'F5_ranking', 'BASELINE_still_40pct_dead']

const rows = ref<CoverageRow[]>([])
const buckets = ref<BucketSummary | null>(null)
const loadError = ref('')

onMounted(async () => {
  try {
    ;[rows.value, buckets.value] = await Promise.all([fetchCoverageSummary(), fetchBucketSummary()])
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : String(e)
  }
})

const orderedRows = computed(() =>
  ORDER.map((key) => ({ key, row: rows.value.find((r) => r.failure_class === key) ?? null, prose: PROSE[key] })),
)

// The nowhere BAND, never one end (001-part-b/SPEC.md §9 / CLAUDE.md): the
// low end credits nothing to the can't-tell dead ends, the high end credits
// all of them. Both ends are computed here from the live sums above — neither
// is a number typed into this file.
const nowherePct = computed(() => {
  if (!buckets.value || buckets.value.total === 0) return null
  const low = (buckets.value.nowhere / buckets.value.total) * 100
  const high = ((buckets.value.nowhere + buckets.value.cant_tell) / buckets.value.total) * 100
  return { low, high }
})
</script>

<template>
  <section class="coverage">
    <h2>Every query type Part A found, including the ones search cannot fix</h2>
    <p v-if="loadError" class="err">Could not load the coverage table: {{ loadError }}</p>

    <table class="cov-table">
      <thead>
        <tr>
          <th>Part A class</th>
          <th>Pairs / searches</th>
          <th>Prototype behaviour</th>
          <th>Demo query</th>
          <th>Fixable by search?</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="({ row, prose }) in orderedRows" :key="prose.label">
          <td><strong>{{ prose.label }}</strong></td>
          <td class="num">{{ row ? `${row.pairs} / ${row.searches.toLocaleString()}` : '—' }}</td>
          <td>{{ prose.behaviour }}</td>
          <td>{{ prose.demo }}</td>
          <td>{{ prose.fixable }}</td>
        </tr>
        <tr>
          <td><strong>F6 — intent-type confusion</strong></td>
          <td class="num">live only</td>
          <td>&mdash;</td>
          <td>&mdash;</td>
          <td><strong>Cut:</strong> no Goods in this catalogue</td>
        </tr>
      </tbody>
    </table>

    <div v-if="buckets && nowherePct" class="where">
      <h3>Where was the answer?</h3>
      <ul>
        <li><strong>Nowhere in the market:</strong> {{ buckets.nowhere.toLocaleString() }} dead ends
          (<strong>{{ nowherePct.low.toFixed(1) }}%–{{ nowherePct.high.toFixed(1) }}%</strong> — a
          band, not a point: the {{ buckets.cant_tell.toLocaleString() }} can&rsquo;t-tell dead ends
          move together under one judgement, and quoting either end alone misstates it)</li>
        <li><strong>The user&rsquo;s own city:</strong> {{ buckets.same_city.toLocaleString() }} dead ends — search's real size</li>
        <li>
          <strong>Another city in the market:</strong> {{ buckets.another_city.toLocaleString() }} dead ends
          <p class="sub-note">
            The <code>city_empty</code> render state answers this same question — the market has it,
            this city does not — but only as a live, per-search fact (a vector score against this
            city's stock), not as a member of this count. F1&ndash;F6 is a cut by <em>mechanism</em>
            and has no cell for this; only this <em>location</em> cut does, which is why the state had
            to be added during the build rather than derived from the taxonomy. Different method,
            different denominator: title-matching the log vs. scoring every search live. Its own count
            is never added to this one.
          </p>
        </li>
        <li><strong>Can&rsquo;t tell from this catalogue:</strong> {{ buckets.cant_tell.toLocaleString() }} dead ends, not attributed</li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.coverage {
  margin: 2.5rem 0;
}

h2 {
  font-size: 1.25rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-text);
  margin: 0 0 1rem;
}

.err {
  color: var(--gp-text);
  font-size: 0.875rem;
}

.cov-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.cov-table th {
  text-align: left;
  font-weight: 800;
  border-bottom: 1px solid var(--gp-separator);
  padding: 0.5rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--gp-text-muted);
}

.cov-table td {
  padding: 0.5rem;
  border-bottom: 1px solid var(--gp-separator);
  vertical-align: top;
}

.num {
  font-family: var(--gp-font-mono);
  white-space: nowrap;
}

.where {
  margin-top: 1.5rem;
}

.where h3 {
  font-size: 1rem;
  font-weight: var(--gp-heading-weight);
  margin: 0 0 0.5rem;
}

.where ul {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.875rem;
  color: var(--gp-text);
}

.where li {
  margin-bottom: 0.375rem;
}

.sub-note {
  margin: 0.25rem 0 0;
  font-size: 0.8125rem;
  color: var(--gp-text-muted);
  max-width: 68ch;
}

.sub-note code {
  font-family: var(--gp-font-mono);
  font-size: 0.75rem;
  background: var(--gp-surface);
  padding: 0.0625rem 0.3125rem;
  border-radius: var(--gp-radius-badge);
}
</style>
