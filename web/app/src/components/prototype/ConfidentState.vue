<script setup lang="ts">
import type { FullSearchResult } from '@/types/search'
import ResultsHeading from './ResultsHeading.vue'
import DealGrid from './DealGrid.vue'

// DESIGN-SYSTEM.md §8.2: plain grid, no banner, no annotation — silence IS the
// confident signal. The one disclosure this state is allowed is normalisation
// (F2, `010-screens/SPEC.md` demo query `masaz tajski`): stated as a fact, not
// styled as a confidence device, because hiding a resolved typo would be its
// own small silent substitution.
defineProps<{
  result: FullSearchResult
}>()
</script>

<template>
  <ResultsHeading :query="result.query" :count="result.available" />
  <p v-if="result.normalised" class="normalised">
    We matched <strong>{{ result.resolved_to }}</strong>.
  </p>
  <DealGrid :deals="result.results" />
</template>

<style scoped>
.normalised {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  color: var(--gp-text-muted);
}
</style>
