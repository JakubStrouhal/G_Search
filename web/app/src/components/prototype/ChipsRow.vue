<script setup lang="ts">
import { computed } from 'vue'
import chipsFixture from '@fixtures/chips.json'
import type { ChipsFixture } from '@/types/chips'

// 010-screens/SPEC.md criterion 1: every state reachable by a named chip.
// Chips carry their own market+city and set the selector before submitting —
// "context before meaning" (decision 4) — free text stays open beside them.
//
// Grouped by expect.render_state, NOT expect.band: they deliberately disagree
// (escape room GB·Birmingham is band=confident, render_state=near_empty), and
// grouping by band would put a near-empty demo under "confident", hiding the
// exact precedence rule this page exists to demonstrate.
const DATA = chipsFixture as unknown as ChipsFixture

const emit = defineEmits<{
  pick: [{ market: string; city: string; query: string }]
}>()

const GROUPS: { key: string; label: string }[] = [
  { key: 'confident', label: 'Confident' },
  { key: 'adjacent', label: 'Labelled adjacency' },
  { key: 'near_empty', label: 'Near-empty' },
  { key: 'abstain', label: 'Honest empty' },
  // Added with the city_empty state (010-screens/SPEC.md amendment). Without
  // this key the group filter below silently drops `be`'s city_empty chips
  // (`hair colour` GB·Birmingham) — found by checking the fixture against
  // this list rather than assuming a new render_state value has a home here.
  { key: 'city_empty', label: 'City empty' },
]

const grouped = computed(() =>
  GROUPS.map((g) => ({
    ...g,
    chips: DATA.chips.filter((c) => c.expect.render_state === g.key),
  })).filter((g) => g.chips.length > 0),
)
</script>

<template>
  <div class="chips">
    <div v-for="g in grouped" :key="g.key" class="group">
      <span class="label">{{ g.label }}</span>
      <button
        v-for="c in g.chips"
        :key="c.id"
        type="button"
        class="chip"
        @click="emit('pick', { market: c.market, city: c.city, query: c.query })"
      >
        {{ c.query }} <span class="loc">{{ c.market }}&middot;{{ c.city }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.chips {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  margin: 1rem 0 1.5rem;
}

.group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.label {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--gp-text-muted);
  margin-right: 0.25rem;
  flex-shrink: 0;
  width: 8rem;
}

.chip {
  height: 2rem;
  padding: 0 0.75rem;
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-pill);
  background: var(--gp-surface);
  color: var(--gp-text);
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  transition:
    background var(--gp-duration) var(--gp-ease),
    border-color var(--gp-duration) var(--gp-ease);
}

.chip:hover {
  background: var(--gp-bg);
  border-color: var(--color-neutral-400);
}

.loc {
  font-weight: 400;
  color: var(--gp-text-muted);
}
</style>
