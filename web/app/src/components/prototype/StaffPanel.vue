<script setup lang="ts">
import type { SearchDealsResponse } from '@/types/search'
import DealGrid from './DealGrid.vue'

// DESIGN-SYSTEM.md §8.7 — deliberately not Groupon: dark, monospace, 420px
// slide-over, default open (010-screens/SPEC.md decision 5 — hiding it by
// default hides the deliverable). Every number here is read off `staff`,
// never re-derived or retyped (D1: the class comes from query_classes via the
// RPC, never from the threshold comparison itself).
//
// `open` is a v-model, not local state: a fixed, default-open 420px panel
// that the page layout does not know about overlaps live content underneath
// it (P0, coordinator's browser check, 2026-08-07 — six elements ran behind
// it at 1280x720, including the abstain panel's own headline cut mid-word).
// PrototypePage reserves the inset off the same boolean this toggles.
const props = defineProps<{
  phase: 'idle' | 'loading' | 'error' | 'result'
  result: SearchDealsResponse | null
  errorMessage: string
  market: string
  city: string
}>()

const open = defineModel<boolean>('open', { default: true })

const UNKNOWN = 'The log records a result count only — no query→deal mapping and no relevance ' +
  'score exist. Which deals any search actually returned is inferred from the catalogue, never ' +
  'observed. This panel cannot tell a happy substitution from a generator ignoring relevance.'

// Task #15 (Codex, High finding): this used to read `result.band === 'abstain'`
// alone. city_empty ALSO writes a row but scores confident/adjacent, so that
// check took the else branch and told the truth about abstain while lying
// about city_empty a second after the RPC had written it. Task #17: `be`
// shipped the structural fix — `demand_row_written` (top-level boolean, true
// on every response shape including the two early returns) and
// `staff.demand_source` ('live' | 'city_empty' | null), decided ONCE inside
// search_deals. This function no longer re-derives anything from band or
// city_empty; it only formats the two flags the RPC already handed over.
//
// TRAP (be, confirmed by coordinator): demand_row_written describes THIS
// response only, never a running total — a second click on the same chip
// writes a second row by design (n=1 each, so the seeded month stays
// untouchable). Never assert this against a demand_events count.
function demandRowStatus(r: SearchDealsResponse | null): string {
  if (!r || !r.demand_row_written) return 'Not written.'
  // demand_row_written is `false` (a literal type) on RefusalResult and
  // EmptyResult, so the guard above narrows r to FullSearchResult here —
  // r.staff exists unconditionally.
  const source = r.staff.demand_source
  if (source === 'live') return 'Written — source=live, automatic.'
  if (source === 'city_empty') {
    return (
      'Written — source=city_empty, automatic. A distribution gap, not a semantic one — the ' +
      'market stocks this, this city does not — with a different owner than a live abstention, ' +
      'so it is never folded into that count.'
    )
  }
  return 'Written.'
}
</script>

<template>
  <button type="button" class="toggle" @click="open = !open">
    {{ open ? 'Hide' : 'Show' }} staff view
  </button>
  <aside class="staff" :class="{ on: open }">
    <button type="button" class="close" aria-label="Close staff panel" @click="open = false">&times;</button>

    <template v-if="phase === 'idle'">
      <p class="dim">Run a search to see the matched document, thresholds and Part A's verdict.</p>
    </template>

    <template v-else-if="phase === 'loading'">
      <p class="dim">Searching&hellip;</p>
    </template>

    <template v-else-if="phase === 'error'">
      <h3>Error</h3>
      <div class="box">{{ errorMessage }}</div>
    </template>

    <template v-else-if="result">
      <h3>Query</h3>
      <table>
        <tr><td>raw</td><td>{{ result.query }}</td></tr>
        <tr><td>market / city</td><td>{{ market }} / {{ city }}</td></tr>
        <tr><td>band</td><td>{{ result.band }}</td></tr>
      </table>

      <template v-if="result.band === 'unknown_query'">
        <h3>Refusal</h3>
        <div class="box">{{ result.why }}</div>
        <h3>Demand row</h3>
        <div class="box"><span class="dim">Not written — an unlogged query has no concept to attribute.</span></div>
      </template>

      <template v-else-if="result.band !== 'empty'">
        <h3>Embedding match</h3>
        <table v-if="result.staff.matched">
          <tr><td>title</td><td>{{ result.staff.matched.title }}</td></tr>
          <tr><td>similarity</td><td>{{ result.staff.matched.similarity.toFixed(4) }}</td></tr>
          <tr><td>doc</td><td class="wrap">{{ result.staff.matched.doc }}</td></tr>
        </table>

        <h3>Market vs. city stock</h3>
        <div class="box" :class="{ finding: result.city_empty }">
          <table>
            <tr><td>market_max_similarity</td><td>{{ result.staff.market_max_similarity ?? '—' }}</td></tr>
            <tr><td>available (this city)</td><td>{{ result.available }}</td></tr>
            <tr><td>city_empty</td><td>{{ result.city_empty }}</td></tr>
          </table>
          <p v-if="result.city_empty" class="finding-label">
            The market scores confident/adjacent on this query — this city stocks none of it. The
            band alone could never have shown this; it is why city_empty exists as its own state.
          </p>
        </div>

        <h3>Thresholds &amp; calibration</h3>
        <table>
          <tr><td>low</td><td>{{ result.staff.low }}</td></tr>
          <tr><td>high</td><td>{{ result.staff.high }}</td></tr>
          <tr><td>alt_floor</td><td>{{ result.staff.alt_floor }}</td></tr>
          <tr><td>alt_max</td><td>{{ result.staff.alt_max ?? '—' }}</td></tr>
          <tr><td>false_confident</td><td>{{ (result.staff.false_confident * 100).toFixed(2) }}%</td></tr>
          <tr><td>false_abstain</td><td>{{ (result.staff.false_abstain * 100).toFixed(2) }}%</td></tr>
          <tr><td>model</td><td class="wrap">{{ result.staff.model }}</td></tr>
          <tr><td>calibrated_on</td><td>{{ result.staff.calibrated_on }}</td></tr>
        </table>

        <h3>Part A</h3>
        <table v-if="result.staff.part_a_logged_here && !result.staff.thin_label">
          <tr><td>concept</td><td>{{ result.staff.part_a_concept ?? '—' }}</td></tr>
          <tr><td>class</td><td>{{ result.staff.part_a_class ?? '—' }}</td></tr>
          <tr><td>coverage</td><td>{{ result.staff.part_a_coverage ?? '—' }}</td></tr>
          <tr>
            <td>agrees with band</td>
            <td :class="{ absent: result.staff.band_agrees_with_part_a === false }">
              {{ result.staff.band_agrees_with_part_a === null ? '—' : result.staff.band_agrees_with_part_a }}
            </td>
          </tr>
        </table>
        <div v-else-if="result.staff.thin_label" class="box">
          <span class="dim">Excluded: the concept map misfires on this query (thin_n row) — showing
          it here would attach a real number to a wrong concept.</span>
        </div>
        <div v-else class="box">
          <span class="dim">Not logged in {{ market }} — query_embeddings is keyed on the query alone
          (613 rows) while query_classes is keyed on (market, query). Part A has no verdict here; no
          June figure is printed for this cell.</span>
        </div>

        <h3>Cross-city gate (S6a)</h3>
        <div class="box">
          <span class="dim">Suppressed on every row. The proposed travel-offer price gate is not
          cleared by this catalogue at any meaningful volume (Part A, `validate.py` — figures live in
          the analysis, not in a queryable table this app can read, so none is repeated here).
          Production recommendation only, never a screen.</span>
        </div>

        <h3>Demand row</h3>
        <div class="box">{{ demandRowStatus(result) }}</div>

        <h3>What today&rsquo;s system would have shown</h3>
        <p class="illustrative">Illustrative, never historical — the log records a count, not which deals a query returned.</p>
        <div class="compare">
          <div class="col today">
            <h4>Today (unlabelled)</h4>
            <!-- The real, unmodified Groupon card, on its own light patch —
                 §8.7: the contrast only lands if this side is visually
                 authentic, which means light-on-white, not staff-dark. -->
            <DealGrid
              v-if="result.band !== 'abstain' && result.results.length"
              :deals="result.results.slice(0, 2)"
            />
            <p v-else-if="result.alternatives.length" class="small">
              A carousel of the closest stocked titles, presented with no label that a substitution
              happened — exactly what §8.4 argues against.
            </p>
            <p v-else class="small">No stocked title is close enough to build a carousel from.</p>
          </div>
          <div class="col">
            <h4>This prototype</h4>
            <p class="small">{{ result.band }}{{ result.near_empty ? ' (near-empty override)' : '' }} — labelled, abstention-first where it applies.</p>
          </div>
        </div>

        <h3>What the system does not know</h3>
        <div class="box unknown">{{ UNKNOWN }}</div>
      </template>
    </template>
  </aside>
</template>

<style scoped>
.toggle {
  position: fixed;
  right: 1.5rem;
  bottom: 1.5rem;
  z-index: 20;
  height: 2.375rem;
  padding: 0 1.25rem;
  border: 1px solid var(--gp-brand);
  border-radius: var(--gp-radius-pill);
  background: var(--gp-brand);
  color: var(--gp-bg);
  font-size: 0.8125rem;
  font-weight: 700;
  cursor: pointer;
}

.staff {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: var(--gp-staff-width);
  max-width: 100%;
  background: var(--gp-staff-bg);
  color: var(--gp-staff-fg);
  padding: 1.5rem;
  overflow: auto;
  transform: translateX(100%);
  transition: transform var(--gp-duration) var(--gp-ease);
  z-index: 30;
  font-size: 0.8125rem;
}

.staff.on {
  transform: none;
}

.close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: transparent;
  border: 0;
  color: var(--gp-staff-muted);
  font-size: 1.25rem;
  cursor: pointer;
}

h3 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--gp-staff-muted);
  margin: 1.375rem 0 0.5rem;
}

h3:first-of-type {
  margin-top: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--gp-font-mono);
}

td {
  padding: 0.1875rem 0;
  vertical-align: top;
}

td:first-child {
  color: var(--gp-staff-muted);
  padding-right: 0.75rem;
  white-space: nowrap;
}

td.wrap {
  white-space: normal;
}

.box {
  background: var(--gp-staff-surface);
  border-radius: var(--gp-radius-media);
  padding: 0.75rem 0.875rem;
  margin-top: 0.5rem;
  line-height: 1.5;
}

.box.unknown {
  border-left: 3px solid var(--color-yellow-400);
  /* §8.7: as prominent as the scores next to it — same size, same colour,
     not a footnote in 11px grey. */
  font-size: 0.8125rem;
}

/* Reuses the panel's own existing "notice this" accent (yellow-400 left
   border, already used by .box.unknown) rather than inventing a new colour —
   this is an internal-tool highlight, not a fourth entry in §8.2's public
   confidence grammar, which stays untouched on the user-facing screen. */
.box.finding {
  border-left: 3px solid var(--color-yellow-400);
}

.finding-label {
  margin: 0.625rem 0 0;
  font-size: 0.8125rem;
  color: var(--gp-staff-fg);
}

.absent {
  color: var(--color-yellow-400);
}

.dim {
  color: var(--gp-staff-muted);
}

.small {
  font-size: 0.75rem;
}

.illustrative {
  margin: 0 0 0.5rem;
  font-size: 0.75rem;
  color: var(--gp-staff-muted);
  font-style: italic;
}

.compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.col {
  border: 1px solid var(--color-neutral-800);
  border-radius: var(--gp-radius-media);
  padding: 0.625rem 0.75rem;
}

.col.today {
  /* Real Groupon card treatment: light surface inside the dark panel, because
     the comparison only lands if this side looks like the actual site. */
  background: var(--gp-bg);
  color: var(--gp-text);
}

.col h4 {
  margin: 0 0 0.375rem;
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--gp-staff-muted);
}

.col.today h4 {
  color: var(--gp-text-muted);
}

.col.today .small {
  color: var(--gp-text-muted);
}
</style>
