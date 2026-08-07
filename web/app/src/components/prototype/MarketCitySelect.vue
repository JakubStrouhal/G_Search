<script setup lang="ts">
import { computed } from 'vue'
import type { MarketCity } from '@/lib/cities'

// Persistent market+city selector (010-screens/SPEC.md decision 4): all 20
// combos, default GB·London, chips override it. The list is passed in from
// public.cities rather than fetched here, so PrototypePage owns one load and
// this stays a plain controlled component.
const props = defineProps<{
  cities: MarketCity[]
  market: string
  city: string
}>()

const emit = defineEmits<{
  'update:market': [string]
  'update:city': [string]
}>()

const markets = computed(() => [...new Set(props.cities.map((c) => c.market))].sort())
const citiesForMarket = computed(() =>
  props.cities.filter((c) => c.market === props.market).map((c) => c.city),
)

function onMarketChange(e: Event) {
  const market = (e.target as HTMLSelectElement).value
  emit('update:market', market)
  const first = props.cities.find((c) => c.market === market)?.city
  if (first) emit('update:city', first)
}
</script>

<template>
  <div class="selector">
    <select :value="market" aria-label="Market" @change="onMarketChange">
      <option v-for="m in markets" :key="m" :value="m">{{ m }}</option>
    </select>
    <span class="sep">·</span>
    <select :value="city" aria-label="City" @change="emit('update:city', ($event.target as HTMLSelectElement).value)">
      <option v-for="c in citiesForMarket" :key="c" :value="c">{{ c }}</option>
    </select>
  </div>
</template>

<style scoped>
.selector {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  height: 2rem;
  padding: 0 0.75rem;
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-pill);
  background: var(--gp-surface);
}

.sep {
  color: var(--gp-text-decorative);
}

select {
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--gp-text);
  cursor: pointer;
}

select:focus-visible {
  outline: 2px solid var(--gp-brand);
  outline-offset: 2px;
}
</style>
