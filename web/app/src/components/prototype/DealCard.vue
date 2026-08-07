<script setup lang="ts">
import type { DealResult } from '@/types/search'

// Groupon's own deal card, copied proportionally (DESIGN-SYSTEM.md §5): 16:9
// image at --radius-xs (8px), no card border, no shadow, radius lives on the
// image only. Reused unmodified by confident, adjacent and near-empty — the
// labelling around it is what changes state, never the card (§8.4).
//
// No merchant name: deals.csv carries no merchant field, so the metadata line
// is city + category, which is real data rather than an invented brand.
// No "was" price: there is one price_usd column, no discount source — showing
// a struck-through price would fabricate a markdown that does not exist
// (web/mock/build.py carries the same rule).
// Similarity is opt-in: confident renders none of it (silence is the signal,
// §8.2); adjacent and near-empty pass it because the SPEC requires "each with
// similarity shown".
const props = defineProps<{
  deal: DealResult
  showSimilarity?: boolean
}>()

const stars = (rating: number | null) => {
  if (rating == null) return null
  const full = Math.round(rating)
  return { full, empty: 5 - full }
}
</script>

<template>
  <article class="deal-card">
    <div class="media">
      <span v-if="deal.is_bookable" class="badge">Bookable online</span>
    </div>
    <p class="meta">{{ deal.city }}</p>
    <h3 class="title">{{ deal.title }}</h3>
    <p v-if="stars(deal.rating)" class="rating">
      <span class="stars" aria-hidden="true">
        {{ '★'.repeat(stars(deal.rating)!.full) }}{{ '☆'.repeat(stars(deal.rating)!.empty) }}
      </span>
      <span class="val">{{ deal.rating!.toFixed(1) }}</span>
      <span class="n">({{ deal.num_ratings.toLocaleString() }})</span>
    </p>
    <p class="price"><span class="now">${{ deal.price_usd.toFixed(2) }}</span></p>
    <p v-if="props.showSimilarity" class="similarity">match {{ deal.similarity.toFixed(2) }}</p>
  </article>
</template>

<style scoped>
.deal-card {
  display: flex;
  flex-direction: column;
}

.media {
  position: relative;
  aspect-ratio: 16 / 9;
  border-radius: var(--gp-radius-media);
  background: var(--gp-surface);
}

.badge {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  background: var(--gp-bg);
  color: var(--gp-text);
  font-size: 0.8125rem;
  font-weight: 700;
  border-radius: var(--gp-radius-badge);
  padding: 0.0625rem 0.375rem;
}

.meta {
  margin: 0.625rem 0 0;
  font-size: 0.8125rem;
  color: var(--gp-text-muted);
}

.title {
  margin: 0.125rem 0 0;
  font-size: 1rem; /* --text-dealCardTitle */
  line-height: 1.375rem;
  font-weight: 700;
  color: var(--gp-text);
  display: -webkit-box;
  -webkit-line-clamp: 3; /* §9: allow three lines, not two — German compounds */
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rating {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
  display: flex;
  gap: 0.3125rem;
  align-items: center;
}

.stars {
  color: var(--gp-star);
  letter-spacing: -1px;
}

.val {
  font-weight: 800;
  color: var(--gp-text);
}

.n {
  color: var(--gp-text-muted);
}

.price {
  margin: 0.375rem 0 0;
  font-size: 0.875rem; /* --text-priceSmall */
  font-weight: 800;
}

.now {
  color: var(--gp-price);
}

.similarity {
  margin: 0.1875rem 0 0;
  font-size: 0.75rem;
  font-family: var(--gp-font-mono);
  color: var(--gp-text-muted);
}
</style>
