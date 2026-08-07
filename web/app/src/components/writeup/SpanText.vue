<script setup lang="ts">
// One inline run of the writeup: plain text, bold, italic or code.
//
// The generator (011-writeup/build_writeup.py) emits spans rather than an HTML
// string precisely so nothing here needs v-html. The writeup is prose from a
// file on disk; rendering it through v-html would be a needless injection
// surface for zero gain.
export type Span = { t: string; v: string }

defineProps<{ spans: Span[] }>()
</script>

<template>
  <template v-for="(s, i) in spans" :key="i">
    <strong v-if="s.t === 'strong'">{{ s.v }}</strong>
    <em v-else-if="s.t === 'em'">{{ s.v }}</em>
    <code v-else-if="s.t === 'code'">{{ s.v }}</code>
    <template v-else>{{ s.v }}</template>
  </template>
</template>
