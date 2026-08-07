<script setup lang="ts">
import wordmarkUrl from '@design/assets/groupon-wordmark.svg'
import type { MarketCity } from '@/lib/cities'
import SearchBar from './SearchBar.vue'
import MarketCitySelect from './MarketCitySelect.vue'

// White header, wordmark left, pill search field, market/city selector beside
// it — DESIGN-SYSTEM.md §5. Not the full 176px promo-bar/nav header measured
// on the live page: this prototype is one search surface, not the homepage,
// and §8 licenses reuse of the search pattern, not an invented category nav.
defineProps<{
  cities: MarketCity[]
  market: string
  city: string
  query: string
}>()

defineEmits<{
  'update:market': [string]
  'update:city': [string]
  'update:query': [string]
  submit: [string]
}>()
</script>

<template>
  <header class="hdr">
    <div class="hdr-in">
      <img :src="wordmarkUrl" width="133" height="22" alt="Groupon" />
      <SearchBar
        :model-value="query"
        placeholder="Search deals"
        @update:model-value="$emit('update:query', $event)"
        @submit="$emit('submit', $event)"
      />
      <MarketCitySelect
        :cities="cities"
        :market="market"
        :city="city"
        @update:market="$emit('update:market', $event)"
        @update:city="$emit('update:city', $event)"
      />
    </div>
  </header>
</template>

<style scoped>
.hdr {
  border-bottom: 1px solid var(--gp-separator);
  background: var(--gp-bg);
}

.hdr-in {
  max-width: 75rem; /* 1200px content column, §4 */
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}
</style>
