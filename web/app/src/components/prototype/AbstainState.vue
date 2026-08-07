<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FullSearchResult } from '@/types/search'
import { fetchCellDemand } from '@/lib/demand'
import { fetchCityCategories } from '@/lib/categories'
import { recordNotifyMe } from '@/lib/demand'
import EmptyPanelIcon from './EmptyPanelIcon.vue'

// DESIGN-SYSTEM.md §8.5 + 010-screens/SPEC.md's five-block abstain sequence,
// IN ORDER — this is the "live risk" the plan calls out: check reads the
// rendered order, not the intent.
//   1. name the gap
//   2. "N searches for this here in June" — seed_searches only, never staff.searches
//   3. "this gap was just recorded" — the automatic source='live' write
//   4. notify-me — the only green on the screen
//   5. labelled alternatives, floored at 0.30 (decision 18)
//
// Deliberately NO "Results for X · 0 deals" heading above this panel (Q1,
// coordinator, 2026-08-07). §8.5's whole argument is that this state is NOT
// Groupon's zero-results screen — and that screen's own furniture IS "Results
// for zzqqxwv" + "0 deals" over an unlabelled substitute carousel (§5's
// screenshot). Stacking the same furniture above the honest panel reads as
// the page agreeing with itself twice, and duplicates the query name the
// panel's own h2 already states. Kept on NearEmptyState, where it stays true:
// that state genuinely has 1-2 real matches, so "N deals" is not a claim this
// page is about to contradict one line down. When city_empty (Q2) ships, that
// state DOES belong under this heading — it is a genuine results-page context
// (market-confident, city-empty) where the count is honestly zero.
const props = defineProps<{
  result: FullSearchResult
  market: string
  city: string
}>()

const seedSearches = ref<number | null>(null)
const seedLoading = ref(true)
const categories = ref<string[]>([])
const categoriesLoading = ref(false)

const notifyState = ref<'idle' | 'sending' | 'done' | 'error'>('idle')
const notifyError = ref('')

async function load() {
  notifyState.value = 'idle'
  seedSearches.value = null
  seedLoading.value = true
  categories.value = []

  // Block 2 gate: only a concept Part A actually logged IN THIS MARKET, and
  // never a thin_n concept (CLAUDE.md — the classifier's concept map misfires
  // on typos; every affected row is n=1, and the panel must not show a
  // visibly wrong concept attached to a real number).
  const concept = props.result.staff.part_a_concept
  if (props.result.staff.part_a_logged_here && !props.result.staff.thin_label && concept) {
    try {
      const cell = await fetchCellDemand(props.market, props.city, concept)
      seedSearches.value = cell?.seed_searches ?? null
    } catch {
      seedSearches.value = null
    }
  }
  seedLoading.value = false

  // Block 5's suppressed branch needs category links.
  if (!props.result.alternatives_above_floor) {
    categoriesLoading.value = true
    try {
      categories.value = await fetchCityCategories(props.market, props.city)
    } catch {
      categories.value = []
    } finally {
      categoriesLoading.value = false
    }
  }
}

watch(
  () => [props.market, props.city, props.result.query],
  load,
  { immediate: true },
)

async function onNotify() {
  notifyState.value = 'sending'
  notifyError.value = ''
  try {
    await recordNotifyMe({
      market: props.market,
      city: props.city,
      concept: props.result.staff.part_a_concept,
      rawQuery: props.result.query,
    })
    notifyState.value = 'done'
  } catch (e) {
    notifyState.value = 'error'
    notifyError.value = e instanceof Error ? e.message : String(e)
  }
}
</script>

<template>
  <div class="panel">
    <EmptyPanelIcon />
    <!-- 1. Name the gap. -->
    <h2>We don&rsquo;t stock &ldquo;{{ result.query }}&rdquo; in {{ city }} — and it isn&rsquo;t a search problem</h2>
    <p class="note">No merchant here currently offers this. No ranking change or synonym list recovers a deal that does not exist.</p>

    <!-- 2. N searches in June — seed_searches only. -->
    <p v-if="!seedLoading && seedSearches !== null" class="june">
      <strong>{{ seedSearches }}</strong> {{ seedSearches === 1 ? 'search' : 'searches' }} for this here in June.
    </p>

    <!-- 3. Automatic write confirmation. -->
    <p class="recorded">
      <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-miterlimit="10"><path d="M4 10 L8 14 L16 6" /></svg>
      This gap was just recorded — a row now exists for {{ market }}&middot;{{ city }} someone can act on.
    </p>

    <!-- 4. Notify-me: the only green on the screen. -->
    <div class="actions">
      <button type="button" class="btn-primary" :disabled="notifyState === 'sending' || notifyState === 'done'" @click="onNotify">
        {{ notifyState === 'done' ? 'Recorded' : 'Notify me if this appears' }}
      </button>
    </div>
    <p v-if="notifyState === 'done'" class="notified">Thanks — that request is now separate from the automatic count above.</p>
    <p v-if="notifyState === 'error'" class="notify-error">Could not record that: {{ notifyError }}</p>
  </div>

  <!-- 5. Labelled alternatives, floored at 0.30 (decision 18). -->
  <div v-if="result.alternatives_above_floor" class="alternatives">
    <h3>Closest things we do stock —</h3>
    <p class="caveat">Not the answer to &ldquo;{{ result.query }}&rdquo;. Ranked by similarity, not relevance.</p>
    <ul class="alt-list">
      <li v-for="a in result.alternatives" :key="a.title">
        <span class="alt-title">{{ a.title }}</span>
        <span class="alt-meta">{{ a.category_l2 }} &middot; {{ a.deal_count }} {{ a.deal_count === 1 ? 'deal' : 'deals' }} &middot; match {{ a.similarity.toFixed(2) }}</span>
      </li>
    </ul>
  </div>
  <div v-else class="alternatives suppressed">
    <h3>Nothing here is close to &ldquo;{{ result.query }}&rdquo;.</h3>
    <p class="caveat">
      Here is what {{ city }} does stock<span v-if="!categoriesLoading && categories.length">:</span>
    </p>
    <ul v-if="!categoriesLoading" class="cat-list">
      <li v-for="c in categories" :key="c">{{ c }}</li>
    </ul>
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

.june {
  margin: 0.875rem auto 0;
  font-size: 0.875rem;
  color: var(--gp-text);
}

.recorded {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.875rem auto 0;
  padding: 0.5rem 0.75rem;
  background: var(--gp-demand-bg);
  border: 1px solid var(--gp-demand-border);
  color: var(--gp-demand-fg);
  border-radius: var(--gp-radius-badge);
  font-size: 0.8125rem;
  font-weight: 700;
}

.actions {
  margin-top: 1.25rem;
}

.btn-primary {
  height: 2.375rem;
  padding: 0 1.25rem;
  border: 1px solid var(--gp-brand);
  border-radius: var(--gp-radius-pill);
  background: var(--gp-brand);
  color: var(--gp-bg);
  font-size: 0.8125rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-primary:disabled {
  cursor: default;
  opacity: 0.85;
}

.notified {
  margin: 0.625rem 0 0;
  font-size: 0.8125rem;
  color: var(--gp-demand-fg);
}

.notify-error {
  margin: 0.625rem 0 0;
  font-size: 0.8125rem;
  color: var(--gp-text);
}

.alternatives {
  background: var(--gp-adjacent-bg);
  border: 1px solid var(--gp-adjacent-border);
  border-radius: var(--gp-radius-panel);
  padding: 1.25rem 1.5rem;
}

.alternatives.suppressed {
  background: var(--gp-surface);
  border-color: var(--gp-separator);
}

.alternatives h3 {
  margin: 0;
  font-size: 1.125rem; /* --text-h4 */
  line-height: 1.375rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-text);
}

.caveat {
  margin: 0.5rem 0 0;
  font-size: 0.8125rem;
  color: var(--gp-text-muted);
}

.alt-list,
.cat-list {
  list-style: none;
  margin: 0.875rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.alt-list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.875rem;
}

.alt-title {
  font-weight: 700;
  color: var(--gp-text);
}

.alt-meta {
  font-family: var(--gp-font-mono);
  font-size: 0.75rem;
  color: var(--gp-text-muted);
  flex-shrink: 0;
}

.cat-list {
  flex-direction: row;
  flex-wrap: wrap;
}

.cat-list li {
  padding: 0.25rem 0.75rem;
  background: var(--gp-bg);
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-pill);
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--gp-text);
  text-transform: capitalize;
}
</style>
