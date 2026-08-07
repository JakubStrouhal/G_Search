<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FullSearchResult } from '@/types/search'
import { fetchCellDemand, recordNotifyMe } from '@/lib/demand'
import { fetchCityCategories } from '@/lib/categories'
import EmptyPanelIcon from './EmptyPanelIcon.vue'

// city_empty — a sixth render state, added as a 010-screens/SPEC.md amendment
// (coordinator, 2026-08-07): the market scored above LOW (this concept IS
// stocked somewhere in the market) but THIS city stocks none of it. Found by
// checking reachability of the precedence rule as originally written: 424 of
// 12,260 city×query combos (92 confident-band, 332 adjacent-band) fell
// through it and would otherwise have rendered `Results for "X"` over an
// empty grid — the exact silent-empty-page failure this build exists to
// prevent. `be` added `city_empty` + `staff.market_max_similarity`
// (screens_city_empty migration) and writes its own demand source
// (`source='city_empty'`, distinct from abstain's `'live'` — folding a
// distribution gap into a figure labelled "abstentions" would mislabel a
// number already on screen, per that migration's own reasoning).
//
// Same family as abstain (§8.5's panel geometry, reused, not a fourth
// confidence colour), THREE rules that make it NOT abstain's copy verbatim:
//   1. No "Results for X" heading — coordinator overruled my own
//      near-empty-style argument here: available IS 0, and that heading over
//      an empty grid is *literally* Groupon's zero-results screen (§5). The
//      panel leads, exactly as on abstain.
//   2. No "and it isn't a search problem" — false here. The market stocks
//      this; only the city does not.
//   3. No cross-city claim, in any form, ever — not "try another city", not
//      a hint. That copy was CUT once already and INDEX #12 records it was
//      false for 315 of 321 rows. The user gets "nothing here", full stop.
//      The market-vs-city contrast is staff-only (StaffPanel.vue).
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

watch(() => [props.market, props.city, props.result.query], load, { immediate: true })

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
  <!-- No "Results for X" heading (rule 1) — the panel leads. -->
  <div class="panel">
    <EmptyPanelIcon />
    <!-- 1. Name the query and the city. Nothing more (rule 2: no "isn't a
         search problem" — the market does stock this). -->
    <h2>Nothing in {{ city }} matches &ldquo;{{ result.query }}&rdquo;.</h2>
    <p class="note">No merchant in {{ city }} currently offers this.</p>

    <!-- 2. N searches in June — seed_searches only, same gate as abstain. -->
    <p v-if="!seedLoading && seedSearches !== null" class="june">
      <strong>{{ seedSearches }}</strong> {{ seedSearches === 1 ? 'search' : 'searches' }} for this here in June.
    </p>

    <!-- 3. Automatic write confirmation (source='city_empty', distinct from
         abstain's 'live' — the copy stays qualitative; the source is a
         staff-only fact per the view's own comment). -->
    <p class="recorded">
      <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-miterlimit="10"><path d="M4 10 L8 14 L16 6" /></svg>
      This gap was just recorded — a row now exists for {{ market }}&middot;{{ city }} someone can act on.
    </p>

    <!-- 4. Notify-me: the only green on the screen, same as abstain. -->
    <div class="actions">
      <button type="button" class="btn-primary" :disabled="notifyState === 'sending' || notifyState === 'done'" @click="onNotify">
        {{ notifyState === 'done' ? 'Recorded' : 'Notify me if this appears' }}
      </button>
    </div>
    <p v-if="notifyState === 'done'" class="notified">Thanks — that request is now separate from the automatic count above.</p>
    <p v-if="notifyState === 'error'" class="notify-error">Could not record that: {{ notifyError }}</p>
  </div>

  <!-- 5. Labelled alternatives, floored exactly as on abstain (rule 5). -->
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
  font-size: 1.125rem;
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
