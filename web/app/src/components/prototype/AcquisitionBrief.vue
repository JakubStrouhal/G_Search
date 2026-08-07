<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { fetchUnmetDemand, fetchS2p, type DemandCell } from '@/lib/acquisitionBrief'

// 001-part-b/SPEC.md §5 — "the demand table IS the merchant acquisition feed."
// Aggregate table (all unmet-demand cells) + one computed brief on the top
// cell. Everything numeric here is a live sum; nothing is typed from the
// SPEC's own worked example, even though that example (GB · London ·
// adrenaline, 222) is exactly what this query returns today.
const cells = ref<DemandCell[]>([])
const s2p = ref<number | null>(null)
const loadError = ref('')

onMounted(async () => {
  try {
    ;[cells.value, s2p.value] = await Promise.all([fetchUnmetDemand(), fetchS2p()])
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : String(e)
  }
})

const top = computed(() => cells.value[0] ?? null)
const rest = computed(() => cells.value.slice(0, 12))
// Upper bound, never a forecast (001-part-b/SPEC.md §5): recovered searches
// convert worse than organic ones, so this is a ceiling on what the top cell
// is worth, not a promise.
const lostPurchases = computed(() => (top.value && s2p.value != null ? top.value.seed_searches * s2p.value : null))
</script>

<template>
  <section class="brief">
    <h2>Acquisition brief — unmet demand, aggregated by market &times; city &times; concept</h2>
    <p v-if="loadError" class="err">Could not load the demand table: {{ loadError }}</p>
    <p class="lede">
      Every abstention writes a row to <code>demand_events</code>; the June log seeds it so a fresh
      instance shows a real baseline rather than &ldquo;1 search&rdquo;. This table is that write,
      aggregated — the differentiating claim, sitting where Groupon's growth priorities intersect.
    </p>

    <div v-if="top" class="top-cell">
      <h3>Top cell: {{ top.market }} &middot; {{ top.city }} &middot; {{ top.concept }}</h3>
      <p>
        <strong>{{ top.seed_searches.toLocaleString() }}</strong> seed searches in June ·
        <strong>0</strong> deals stocking · <strong>{{ top.live_abstentions }}</strong> live abstentions ·
        <strong>{{ top.city_empty_events }}</strong> city-empty events · <strong>{{ top.notify_requests }}</strong>
        notify-me requests.
      </p>
      <p v-if="lostPurchases !== null" class="upper-bound-note">
        Est. lost purchases &asymp; <strong>{{ Math.round(lostPurchases) }}/month</strong>, an
        <strong>upper bound</strong> — seed searches &times; search-to-purchase rate, computed live
        off <code>query_classes</code> (searches, results and purchases the June log actually
        carries), never typed. Recovered searches convert worse than organic ones, so treat this as a
        ceiling, not a forecast.
      </p>
    </div>

    <table class="demand-table">
      <thead>
        <tr>
          <th>Market</th>
          <th>City</th>
          <th>Concept</th>
          <th class="num">Seed searches (June)</th>
          <th class="num">Live abstentions</th>
          <th class="num">City-empty events</th>
          <th class="num">Notify-me requests</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in rest" :key="`${c.market}-${c.city}-${c.concept}`">
          <td>{{ c.market }}</td>
          <td>{{ c.city }}</td>
          <td>{{ c.concept }}</td>
          <td class="num">{{ c.seed_searches.toLocaleString() }}</td>
          <td class="num">{{ c.live_abstentions }}</td>
          <td class="num">{{ c.city_empty_events }}</td>
          <td class="num">{{ c.notify_requests }}</td>
        </tr>
      </tbody>
    </table>
    <p class="note">
      Four source counts, never summed into one: seed = the June log; live = the market had nothing
      anywhere (automatic); city_empty = the market had it, this city didn't (automatic, a
      distribution gap with a different owner than live); notify_me = button presses, not people.
    </p>
  </section>
</template>

<style scoped>
.brief {
  margin: 2.5rem 0;
}

h2 {
  font-size: 1.25rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-text);
  margin: 0 0 0.75rem;
}

.err {
  color: var(--gp-text);
  font-size: 0.875rem;
}

.lede {
  font-size: 0.9375rem;
  color: var(--gp-text-muted);
  margin: 0 0 1.25rem;
  max-width: 70ch;
}

.top-cell {
  background: var(--gp-surface);
  border-radius: var(--gp-radius-panel);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}

.top-cell h3 {
  margin: 0 0 0.5rem;
  font-size: 1.125rem;
  font-weight: var(--gp-heading-weight);
}

.top-cell p {
  margin: 0.25rem 0 0;
  font-size: 0.9375rem;
}

.upper-bound-note {
  margin-top: 0.75rem !important;
  font-size: 0.8125rem !important;
  color: var(--gp-text-muted);
  max-width: 65ch;
}

.demand-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.demand-table th {
  text-align: left;
  font-weight: 800;
  border-bottom: 1px solid var(--gp-separator);
  padding: 0.5rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--gp-text-muted);
}

.demand-table td {
  padding: 0.5rem;
  border-bottom: 1px solid var(--gp-separator);
}

.num {
  text-align: right;
  font-family: var(--gp-font-mono);
}

.note {
  margin-top: 0.75rem;
  font-size: 0.8125rem;
  color: var(--gp-text-muted);
}
</style>
