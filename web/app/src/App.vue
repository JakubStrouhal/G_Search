<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef, watch, type Component } from 'vue'
import SiteIndex from '@/components/SiteIndex.vue'
import SignOutButton from '@/components/SignOutButton.vue'

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

// The Part B prototype (010-screens/SPEC.md): same lazy-import discipline as
// #stack and for the same reason — src/config/supabase.ts throws at module
// scope on missing env, so a static import here would blank the front door on
// any deploy whose env is unfilled. #prototype is the door the explainer's
// #demo button and the /app Part B card both open onto.
const prototype = shallowRef<Component>()
const prototypeError = ref('')

watch(
  route,
  async (r) => {
    if (r === '#stack' && !stack.value && !stackError.value) {
      try {
        stack.value = (await import('@/components/HealthCheck.vue')).default
      } catch (e) {
        stackError.value = e instanceof Error ? e.message : String(e)
      }
      return
    }
    if (r === '#prototype' && !prototype.value && !prototypeError.value) {
      try {
        prototype.value = (await import('@/components/prototype/PrototypePage.vue')).default
      } catch (e) {
        prototypeError.value = e instanceof Error ? e.message : String(e)
      }
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
  <template v-else-if="route === '#prototype'">
    <component :is="prototype" v-if="prototype" />
    <p v-else-if="prototypeError" class="stack-error">{{ prototypeError }}</p>
  </template>
  <SiteIndex v-else />

  <!-- Chrome, not a screen — mounted here so it survives the route switch above. -->
  <SignOutButton />
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
