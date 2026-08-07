<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { supabase, supabaseUrl } from '@/config/supabase'

type Verdict = 'checking' | 'ok' | 'key-rejected' | 'unreachable'

const verdict = ref<Verdict>('checking')
const gatewayStatus = ref<string>('…')
const roundTrip = ref<string>('…')
const detail = ref<string>('')

const isLocal = computed(() => /^https?:\/\/(127\.0\.0\.1|localhost)/.test(supabaseUrl))

// Two probes, chosen so they behave the SAME on the local stack and on a hosted
// project. The obvious probe — GET /rest/v1/, the OpenAPI root — does not: hosted
// Supabase answers 401 "Secret API key required" there even when the publishable
// key is perfectly valid, so it reports a broken connection on a working one.
//
// 1. GoTrue's health endpoint. 200 on both. Proves the API gateway is up.
// 2. A select against a table that deliberately does not exist, through the client.
//    While the database is empty, PostgREST's "table not found" (PGRST205) is the
//    correct answer and proves a full round trip. A hosted project rejects a bad
//    key here with 401 "Invalid API key" instead — see the caveat below.
async function probe() {
  try {
    const res = await fetch(`${supabaseUrl}/auth/v1/health`, {
      headers: { apikey: import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY },
    })
    gatewayStatus.value = String(res.status)
    if (!res.ok) {
      verdict.value = 'unreachable'
      detail.value = `Auth gateway answered ${res.status}.`
      return
    }
  } catch (e) {
    verdict.value = 'unreachable'
    gatewayStatus.value = 'no response'
    detail.value = e instanceof Error ? e.message : String(e)
    return
  }

  const { error } = await supabase.from('__no_such_table__').select('*').limit(1)

  if (!error) {
    verdict.value = 'ok'
    roundTrip.value = 'unexpectedly succeeded — a table by that name exists?'
    return
  }

  if (/invalid api key/i.test(error.message)) {
    verdict.value = 'key-rejected'
    roundTrip.value = error.message
    detail.value = 'The endpoint is up but refused the key. Check VITE_SUPABASE_PUBLISHABLE_KEY.'
    return
  }

  verdict.value = 'ok'
  roundTrip.value = `${error.code ?? 'error'} — ${error.message}`
}

const label = computed(() =>
  verdict.value === 'checking'
    ? 'checking…'
    : verdict.value === 'ok'
      ? 'connected'
      : verdict.value === 'key-rejected'
        ? 'key rejected'
        : 'unreachable',
)

onMounted(probe)
</script>

<template>
  <section class="card">
    <p class="eyebrow">Part B · stack init</p>
    <h1>
      Supabase
      <span :class="['pill', verdict]">{{ label }}</span>
    </h1>

    <dl>
      <dt>Target</dt>
      <dd>
        <code>{{ supabaseUrl }}</code>
        <span class="tag">{{ isLocal ? 'local' : 'hosted' }}</span>
      </dd>

      <dt>Auth gateway</dt>
      <dd><code>{{ gatewayStatus }}</code></dd>

      <dt>Round trip via supabase-js</dt>
      <dd><code>{{ roundTrip }}</code></dd>
    </dl>

    <p v-if="detail" class="detail">{{ detail }}</p>

    <p class="note">
      The database is <strong>empty by design</strong> — zero migrations, zero tables. A
      “table not found” above is the pass condition, not a fault.
    </p>

    <p v-if="isLocal" class="note caveat">
      <strong>What this does not prove, locally.</strong> The local stack does not enforce the
      API key — a deliberately wrong key still returns <code>PGRST205</code>, not
      <code>401</code>. So “connected” here means the stack is reachable, and nothing about
      whether the key is correct. Only a hosted project tests that.
    </p>
  </section>
</template>

<style scoped>
.card {
  max-width: 44rem;
  margin: 4rem auto;
  padding: 2rem;
  background: var(--gp-bg);
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-panel);
  box-shadow: var(--gp-shadow-card);
}

.eyebrow {
  margin: 0 0 0.5rem;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--gp-text-muted);
}

h1 {
  margin: 0 0 1.5rem;
  font-family: var(--gp-font-display);
  font-weight: var(--gp-heading-weight);
  font-size: 1.75rem;
  color: var(--gp-text);
}

.pill {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.15em 0.7em;
  border-radius: var(--gp-radius-pill);
  font-family: var(--gp-font);
  font-size: 0.8rem;
  vertical-align: middle;
}
.pill.checking {
  background: var(--gp-surface);
  color: var(--gp-text-muted);
}
.pill.ok {
  background: var(--gp-brand-subtle);
  color: var(--gp-brand);
}
.pill.key-rejected,
.pill.unreachable {
  background: var(--gp-abstain-bg);
  color: var(--gp-abstain-fg);
}

dl {
  display: grid;
  grid-template-columns: minmax(0, 12rem) 1fr;
  gap: 0.5rem 1rem;
  margin: 0 0 1.5rem;
}
dt {
  color: var(--gp-text-muted);
}
dd {
  margin: 0;
  min-width: 0;
}
code {
  font-family: var(--gp-font-mono);
  font-size: 0.85em;
  overflow-wrap: anywhere;
}

.tag {
  margin-left: 0.5rem;
  padding: 0.1em 0.5em;
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-badge);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--gp-text-muted);
}

.detail {
  padding: 0.75rem 1rem;
  background: var(--gp-abstain-bg);
  color: var(--gp-abstain-fg);
  border-radius: var(--gp-radius-badge);
  font-size: 0.9rem;
}

.note {
  margin: 0;
  padding-top: 1.25rem;
  border-top: 1px solid var(--gp-separator);
  color: var(--gp-text-muted);
  font-size: 0.9rem;
  line-height: 1.55;
}
.caveat {
  margin-top: 1.25rem;
}
</style>
