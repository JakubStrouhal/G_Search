<script setup lang="ts">
import type { RefusalResult } from '@/types/search'
import EmptyPanelIcon from './EmptyPanelIcon.vue'

// band=unknown_query: the query is not among the 613 logged, so nothing else
// runs — no scoring, no staff block, no demand write (010-screens/SPEC.md,
// "Refusals write no demand row — an unlogged query has no concept to
// attribute"). §8.5's panel geometry, same as abstain, but neutral: nothing
// has gone wrong here either, the demo simply cannot speak to a string it
// never logged. `why` is quoted VERBATIM from the RPC — this component invents
// no explanation of its own.
defineProps<{
  result: RefusalResult
}>()
</script>

<template>
  <div class="panel">
    <EmptyPanelIcon />
    <h2>&ldquo;{{ result.query }}&rdquo; is outside the logged world</h2>
    <p class="why">{{ result.why }}</p>
    <p class="scope">The logged set covers {{ result.logged_queries }} queries.</p>
  </div>
</template>

<style scoped>
.panel {
  background: var(--gp-abstain-bg);
  border-radius: var(--gp-radius-panel);
  padding: 2.5rem 2rem;
  text-align: center;
  margin-bottom: 1.25rem;
}

h2 {
  margin: 0 auto;
  max-width: 36ch;
  font-size: 1.25rem; /* --text-h3 */
  line-height: 1.5rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-text);
}

.why {
  max-width: 56ch;
  margin: 0.625rem auto 0;
  font-size: 0.9375rem;
  color: var(--gp-text-muted);
}

.scope {
  margin: 0.75rem auto 0;
  font-size: 0.8125rem;
  font-family: var(--gp-font-mono);
  color: var(--gp-text-muted);
}
</style>
