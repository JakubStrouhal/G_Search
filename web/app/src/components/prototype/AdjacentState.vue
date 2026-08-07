<script setup lang="ts">
import { ref } from 'vue'
import type { FullSearchResult } from '@/types/search'
import { recordNotifyMe } from '@/lib/demand'
import ResultsHeading from './ResultsHeading.vue'
import DealGrid from './DealGrid.vue'

// DESIGN-SYSTEM.md §8.4 — purple header strip (the settled geometry in
// web/mock/build.py: text block on #f5edfc / #d8b9f2, plain grid below it,
// unmodified cards). Purple carries "this has a caveat" already (§2's
// promo-code price); never green here — green is reserved for the abstain
// dead-end's one converting action (§11 checklist).
const props = defineProps<{
  result: FullSearchResult
  city: string
  market: string
}>()

const notifyState = ref<'idle' | 'sending' | 'done' | 'error'>('idle')

async function onNotify() {
  notifyState.value = 'sending'
  try {
    await recordNotifyMe({
      market: props.market,
      city: props.city,
      concept: props.result.staff.part_a_concept,
      rawQuery: props.result.query,
    })
    notifyState.value = 'done'
  } catch {
    notifyState.value = 'error'
  }
}
</script>

<template>
  <ResultsHeading :query="result.query" :count="result.available" />
  <div class="adjacent">
    <h2>&ldquo;{{ result.query }}&rdquo;</h2>
    <p class="miss">We don&rsquo;t have &ldquo;{{ result.query }}&rdquo; in {{ city }}.</p>
    <p class="lead">Here&rsquo;s what&rsquo;s closest, which may not be what you meant:</p>
    <button type="button" class="btn-secondary" :disabled="notifyState !== 'idle'" @click="onNotify">
      {{ notifyState === 'done' ? 'Recorded' : 'Notify me if this appears' }}
    </button>
  </div>
  <DealGrid :deals="result.results" :show-similarity="true" />
</template>

<style scoped>
.adjacent {
  background: var(--gp-adjacent-bg);
  border: 1px solid var(--gp-adjacent-border);
  border-radius: var(--gp-radius-panel);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
}

h2 {
  margin: 0;
  font-size: 1.125rem; /* --text-h4 */
  line-height: 1.375rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-adjacent-fg);
}

.miss {
  margin: 0.5rem 0 0;
  font-size: 0.875rem;
  color: var(--gp-text);
}

.lead {
  margin: 0.625rem 0 0;
  font-size: 0.875rem;
  font-weight: 800;
  color: var(--gp-text);
}

.btn-secondary {
  margin-top: 0.875rem;
  height: 2rem;
  padding: 0 1rem;
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-pill);
  background: var(--gp-bg);
  color: var(--gp-text);
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-secondary:disabled {
  cursor: default;
  opacity: 0.85;
}
</style>
