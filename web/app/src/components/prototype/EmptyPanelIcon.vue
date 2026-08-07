<script setup lang="ts">
// DESIGN-SYSTEM.md §8.5 step 1: the same 20x20 square-cap stroke idiom as the
// rest of the icon set, tertiary colour, white circle on the muted surface —
// reusing Groupon's own empty-panel geometry so abstain/refusal/near-empty
// feel native rather than invented from nothing.
</script>

<template>
  <div class="glyph">
    <svg width="28" height="28" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-linecap="square" stroke-miterlimit="10">
      <path d="M3 3 L17 17" />
      <path d="M16 8 L12 4 H4 V12 L8 16" />
    </svg>
  </div>
</template>

<style scoped>
.glyph {
  width: 4rem;
  height: 4rem;
  border-radius: var(--gp-radius-pill);
  background: var(--gp-bg);
  color: var(--gp-abstain-icon);
  display: grid;
  place-items: center;
  margin: 0 auto 1rem;
}
</style>
