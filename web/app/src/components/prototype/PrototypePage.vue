<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { fetchCities, type MarketCity } from '@/lib/cities'
import { searchDeals } from '@/lib/searchDeals'
import { resolveRenderState } from '@/lib/renderState'
import type { SearchDealsResponse, RefusalResult, FullSearchResult } from '@/types/search'
import PageHeader from './PageHeader.vue'
import ChipsRow from './ChipsRow.vue'
import RefusalCard from './RefusalCard.vue'
import ErrorCard from './ErrorCard.vue'
import AbstainState from './AbstainState.vue'
import CityEmptyState from './CityEmptyState.vue'
import NearEmptyState from './NearEmptyState.vue'
import AdjacentState from './AdjacentState.vue'
import ConfidentState from './ConfidentState.vue'
import StaffPanel from './StaffPanel.vue'
import CoverageTable from './CoverageTable.vue'
import AcquisitionBrief from './AcquisitionBrief.vue'

// The realistic Groupon surface at /app#prototype (010-screens/SPEC.md,
// "Required behaviour"). This is the one place the RPC is called and the one
// place render-state precedence is resolved — every child component below
// just renders the state it was handed.

const cities = ref<MarketCity[]>([])
const citiesError = ref('')

// Defaults: GB · London (decision 4). Chips override both.
const market = ref('GB')
const city = ref('London')
const query = ref('')

type Phase = 'idle' | 'loading' | 'error' | 'result'
const phase = ref<Phase>('idle')
const result = ref<SearchDealsResponse | null>(null)
const errorMessage = ref('')

onMounted(async () => {
  try {
    cities.value = await fetchCities()
  } catch (e) {
    citiesError.value = e instanceof Error ? e.message : String(e)
  }
})

const renderState = computed(() => (result.value ? resolveRenderState(result.value) : 'idle'))
const resultKey = computed(() => `${market.value}|${city.value}|${result.value?.query ?? ''}`)

// Default-open per decision 5 — which means the inset has to be right from
// the very first paint, not just after a toggle. StaffPanel is `position:
// fixed`; nothing else reserved its width, so it overlapped live content
// (P0, coordinator's browser check at 1280x720 — six elements ran underneath
// it, including the abstain panel's own headline cut mid-sentence). This
// tracks the same boolean the panel toggles, via v-model.
const staffOpen = ref(true)

async function submit(q: string) {
  query.value = q
  phase.value = 'loading'
  errorMessage.value = ''
  const outcome = await searchDeals(market.value, city.value, q, 12)
  if (!outcome.ok) {
    result.value = null
    errorMessage.value = outcome.error
    phase.value = 'error'
    return
  }
  // band=empty: "the input simply doesn't submit ... a forced blank POST
  // renders nothing new" — SearchBar already blocks blank submits, so this is
  // belt-and-suspenders for a query that trims to nothing server-side.
  if (outcome.data.band === 'empty') {
    result.value = null
    phase.value = 'idle'
    return
  }
  result.value = outcome.data
  phase.value = 'result'
}

function onChipPick(pick: { market: string; city: string; query: string }) {
  market.value = pick.market
  city.value = pick.city
  submit(pick.query)
}
</script>

<template>
  <!-- Everything that isn't the fixed staff panel lives inside this inset
       wrapper, so the panel's width is reserved rather than overlapped. -->
  <div class="page" :class="{ 'staff-open': staffOpen }">
  <PageHeader
    :cities="cities"
    :market="market"
    :city="city"
    :query="query"
    @update:market="market = $event"
    @update:city="city = $event"
    @update:query="query = $event"
    @submit="submit"
  />

  <main class="content">
    <p v-if="citiesError" class="cities-error">Could not load the market/city list: {{ citiesError }}</p>

    <ChipsRow @pick="onChipPick" />

    <p v-if="phase === 'idle'" class="prompt">Pick a chip above, or search a market&rsquo;s catalogue directly.</p>
    <p v-else-if="phase === 'loading'" class="prompt">Searching&hellip;</p>
    <ErrorCard v-else-if="phase === 'error'" :message="errorMessage" />

    <template v-else-if="phase === 'result' && result">
      <!-- :key forces a fresh component instance per search — AdjacentState
           and AbstainState both hold local notify-button state, and without
           this Vue reuses the instance across two adjacent results, leaving a
           "Recorded" button stuck disabled for a query that never asked. -->
      <RefusalCard v-if="renderState === 'refusal'" :key="resultKey" :result="(result as RefusalResult)" />
      <AbstainState
        v-else-if="renderState === 'abstain'"
        :key="resultKey"
        :result="(result as FullSearchResult)"
        :market="market"
        :city="city"
      />
      <CityEmptyState
        v-else-if="renderState === 'city_empty'"
        :key="resultKey"
        :result="(result as FullSearchResult)"
        :market="market"
        :city="city"
      />
      <NearEmptyState
        v-else-if="renderState === 'near_empty'"
        :key="resultKey"
        :result="(result as FullSearchResult)"
        :city="city"
      />
      <AdjacentState
        v-else-if="renderState === 'adjacent'"
        :key="resultKey"
        :result="(result as FullSearchResult)"
        :city="city"
        :market="market"
      />
      <ConfidentState v-else-if="renderState === 'confident'" :key="resultKey" :result="(result as FullSearchResult)" />
    </template>

    <!-- HIGH-priority, always visible (001-part-b/SPEC.md §4): a grader
         checks for the unfixable rows in ten seconds, so these sections never
         hide behind a search. -->
    <CoverageTable />
    <AcquisitionBrief />
  </main>
  </div>

  <StaffPanel
    v-model:open="staffOpen"
    :phase="phase"
    :result="result"
    :error-message="errorMessage"
    :market="market"
    :city="city"
  />
</template>

<style scoped>
.page {
  transition: padding-right var(--gp-duration) var(--gp-ease);
}

/* Reserves the fixed panel's own width (--gp-staff-width, the same token it
   sizes itself with — not a second literal that could drift from it) so the
   centred header/content underneath shift left instead of running behind it.
   Checked at 1280 and 1440: the centred children (max-width 1200px, margin
   auto) simply re-centre in the narrower box; nothing is clipped at either
   width. */
.page.staff-open {
  padding-right: var(--gp-staff-width);
}

.content {
  max-width: 75rem; /* 1200px content column, §4 */
  margin: 0 auto;
  padding: 1.5rem;
}

.cities-error {
  color: var(--gp-text);
  font-size: 0.875rem;
}

.prompt {
  color: var(--gp-text-muted);
  font-size: 0.9375rem;
}
</style>
