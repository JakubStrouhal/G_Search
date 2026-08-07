<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef, watch, type Component } from 'vue'
import SiteIndex from '@/components/SiteIndex.vue'

// One hash, no router. The health check is an operational surface, not a screen of
// the deliverable — it stays reachable at #stack and off the front door.
//
// It is loaded on demand, and that is load-bearing rather than a size optimisation:
// src/config/supabase.ts THROWS at module scope when VITE_SUPABASE_URL is missing, so
// a static import would take the whole page down to a blank screen on any deploy whose
// env is not filled in. The front door must render with no backend configured at all.
const route = ref(location.hash)
const sync = () => (route.value = location.hash)

const stack = shallowRef<Component>()
const stackError = ref('')

watch(
  route,
  async (r) => {
    if (r !== '#stack' || stack.value || stackError.value) return
    try {
      stack.value = (await import('@/components/HealthCheck.vue')).default
    } catch (e) {
      stackError.value = e instanceof Error ? e.message : String(e)
    }
  },
  { immediate: true },
)

onMounted(() => window.addEventListener('hashchange', sync))
onUnmounted(() => window.removeEventListener('hashchange', sync))
</script>

<template>
  <template v-if="route === '#stack'">
    <component :is="stack" v-if="stack" />
    <p v-else-if="stackError" class="stack-error">{{ stackError }}</p>
  </template>
  <SiteIndex v-else />
</template>

<style scoped>
.stack-error {
  max-width: 44rem;
  margin: 4rem auto;
  padding: 1rem 1.25rem;
  background: var(--gp-abstain-bg);
  color: var(--gp-abstain-fg);
  border-radius: var(--gp-radius-badge);
  font-size: 0.9rem;
}
</style>
