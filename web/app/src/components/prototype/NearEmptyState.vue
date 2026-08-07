<script setup lang="ts">
import type { FullSearchResult } from '@/types/search'
import EmptyPanelIcon from './EmptyPanelIcon.vue'
import DealGrid from './DealGrid.vue'
import ResultsHeading from './ResultsHeading.vue'

// DESIGN-SYSTEM.md §8.3 — the headline of the whole analysis, and the one most
// likely to be built wrong by accident: DO NOT render this as a short results
// grid. The panel comes first, full width, unmodified; the 1-2 real deals are
// a footnote below it. `near_empty` OVERRIDES the band that produced it — this
// component renders regardless of whether the RPC called it confident or
// adjacent (chip "escape room" GB·Birmingham is band=confident, near_empty
// still wins).
//
// No conversion-rate figure appears here: the 1.7%/16.1% cliff is a Part A
// number with no column on this response, and CLAUDE.md bans typing a figure
// no query justifies.
defineProps<{
  result: FullSearchResult
  city: string
}>()
</script>

<template>
  <ResultsHeading :query="result.query" :count="result.available" />
  <div class="panel">
    <EmptyPanelIcon />
    <h2>
      This is all we found for &ldquo;{{ result.query }}&rdquo; in {{ city }} — and it may not be
      what you meant
    </h2>
    <p class="note">
      The catalogue holds only {{ result.available }} {{ result.available === 1 ? 'match' : 'matches' }}
      here. A page this thin converts like an empty one, so it is shown as a caveat, not a normal
      results page.
    </p>
  </div>
  <p class="footnote">
    {{ result.available === 1 ? 'The one match' : `Both ${result.available} matches` }}, unmodified:
  </p>
  <DealGrid :deals="result.results" />
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
  max-width: 40ch;
  font-size: 1.25rem;
  line-height: 1.5rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-text);
}

.note {
  max-width: 56ch;
  margin: 0.625rem auto 0;
  font-size: 0.9375rem;
  color: var(--gp-text-muted);
}

.footnote {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--gp-text-muted);
  margin: 0 0 0.625rem;
}
</style>
