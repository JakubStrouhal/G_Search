<script setup lang="ts">
// "Failure is its own honest state" (010-screens/SPEC.md): an RPC error or a
// network failure renders this card quoting the actual message rather than
// being converted into an empty state or an abstention. No spinner-then-retry
// theatre — the form itself is still there to resubmit.
defineProps<{
  message: string
}>()
</script>

<template>
  <div class="panel">
    <h2>The search failed</h2>
    <p class="msg">{{ message }}</p>
    <p class="note">This is not an empty result and not an abstention — the request itself did not complete.</p>
  </div>
</template>

<style scoped>
.panel {
  background: var(--gp-abstain-bg);
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-panel);
  padding: 2rem;
  margin-bottom: 1.25rem;
}

h2 {
  margin: 0 0 0.5rem;
  font-size: 1.25rem;
  line-height: 1.5rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-text);
}

.msg {
  margin: 0;
  font-size: 0.9375rem;
  font-family: var(--gp-font-mono);
  color: var(--gp-text);
}

.note {
  margin: 0.75rem 0 0;
  font-size: 0.8125rem;
  color: var(--gp-text-muted);
}
</style>
