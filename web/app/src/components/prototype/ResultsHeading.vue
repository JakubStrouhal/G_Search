<script setup lang="ts">
// DESIGN-SYSTEM.md §5: <h1>"Results for &quot;query&quot;"</h1> at 24px/800 with
// a right-aligned deal count, present even at zero. This is page furniture
// shared by every band — including abstain, where `available` is 0 by
// construction — so criterion 12's "count present even at zero" holds without
// touching the abstain panel's own block order (§8.5's sequence starts inside
// the panel, one level down from this heading).
defineProps<{
  query: string
  count: number
}>()
</script>

<template>
  <div class="heading">
    <h1>Results for &ldquo;{{ query }}&rdquo;</h1>
    <span class="count">{{ count }} {{ count === 1 ? 'deal' : 'deals' }}</span>
  </div>
</template>

<style scoped>
.heading {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin: 0 0 1rem;
}

h1 {
  margin: 0;
  font-size: 1.5rem; /* --text-h2 */
  line-height: 1.8125rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-text);
}

.count {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 0.8125rem;
  color: var(--gp-text-muted);
}
</style>
