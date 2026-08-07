<script setup lang="ts">
import type { DealResult } from '@/types/search'
import DealCard from './DealCard.vue'

defineProps<{
  deals: DealResult[]
  showSimilarity?: boolean
}>()
</script>

<template>
  <div class="grid">
    <DealCard v-for="d in deals" :key="d.deal_id" :deal="d" :show-similarity="showSimilarity" />
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(13.125rem, 1fr));
  gap: 1.5rem 1.25rem;
}
</style>
