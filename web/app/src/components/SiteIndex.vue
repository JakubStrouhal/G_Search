<script setup lang="ts">
// The deployed front door.
//
// Number-free on purpose: 006-one-page/SPEC.md G6 bans a hand-typed figure in any
// component, and every figure this page could quote already lives on the explainer,
// bound to story_data.json. Statuses are INDEX.md's — an overstated status here is
// the same defect as a stale number.
//
// Design: docs/design/DESIGN-SYSTEM.md. Sentence case (§7); headings at 800 (§3);
// green on the one real action and nowhere else (§2); chips in Groupon's secondary
// button idiom (§5); no elevation, because the homepage barely uses any (§4).
//
// Sized for a 14" laptop — roughly 1512 x 860 CSS px after browser chrome. Everything
// through the footer fits without scrolling at that height, so the three deliverables
// and their real status are visible at once rather than discovered by scrolling. Every
// size below is a token from §3, not a round number that happened to look right.

type Card = {
  part: string
  title: string
  status: string
  live?: boolean
  body: string
  href?: string
  cta?: string
  pending?: string
}

const cards: Card[] = [
  {
    part: 'Part A',
    title: 'What is broken',
    status: 'live',
    live: true,
    body:
      'The supplied search log and catalogue read against each other, then checked ' +
      'against live production. Six chapters, every figure computed by a script rather ' +
      'than typed — including the ones that undercut the headline.',
    href: '/explainer.html',
    cta: 'Open the explainer',
  },
  {
    part: 'Part B',
    title: 'What right looks like',
    status: 'in build',
    body:
      'A clickable prototype that handles every failure class the analysis found, ' +
      'including the ones search cannot fix. What it does when it has no good answer ' +
      'is the point, so abstention comes before results.',
    pending: 'Not yet deployed.',
  },
  {
    part: 'Part C',
    title: 'The writeup',
    status: 'not started',
    body:
      'Two pages: what was found, what was built and why rather than the alternatives, ' +
      'what the platform teams must supply, and what would signal it was not working. ' +
      'Plus the log of hours and of what the AI tools got wrong.',
    pending: 'Not yet written.',
  },
]
</script>

<template>
  <div class="shell">
    <header class="masthead">
      <p class="eyebrow">Case study · R29944 · Senior Product Manager, AI</p>
      <h1>When a search failed, where was the answer?</h1>
      <p class="lede">
        Discovery for Groupon's international markets — the analysis, the prototype it
        produced, and a standing record of what the data cannot establish.
      </p>
    </header>

    <ul class="grid">
      <li v-for="card in cards" :key="card.part">
        <!-- The whole panel is the target where there is somewhere to go: a 13px button
             is a small thing to hit, and the card is the object being chosen. -->
        <component
          :is="card.href ? 'a' : 'div'"
          :href="card.href"
          :class="['panel', { 'panel--link': card.href }]"
        >
          <p class="meta">
            <span class="part">{{ card.part }}</span>
            <span :class="['chip', { 'chip--live': card.live }]">{{ card.status }}</span>
          </p>
          <h2>{{ card.title }}</h2>
          <p class="body">{{ card.body }}</p>
          <span v-if="card.cta" class="btn">{{ card.cta }}</span>
          <span v-else class="pending">{{ card.pending }}</span>
        </component>
      </li>
    </ul>

    <!-- No link to #stack. The route stays reachable by URL, but until the Supabase
         project is hosted it reports a localhost target as unreachable, and a visible
         link invites a reader to click straight into a broken operational panel. It
         goes back when there is a remote project for it to succeed against. -->
    <footer class="foot">
      <p>
        The explainer is self-contained — no server, no kernel, no network. It opens the same
        way from this link or from the file in the repository.
      </p>
    </footer>
  </div>
</template>

<style scoped>
/* Groupon's content column is 1200px (§4). The gutter subtraction keeps it off the
 * bezel on a 14" without a media query. */
.shell {
  width: min(1200px, 100% - 3rem);
  margin: 0 auto;
  padding: 3rem 0 2.5rem;
}

.masthead {
  max-width: 40rem; /* measure, not column width — the lede is the only long line */
  margin-bottom: 2.5rem;
}

.eyebrow {
  margin: 0 0 0.75rem;
  font-size: 0.8125rem; /* --text-xs is 13px here, not 12px (§3) */
  line-height: 1.125rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--gp-text-muted);
}

h1 {
  margin: 0 0 0.75rem;
  font-size: 2rem; /* --text-h1 */
  line-height: 2.375rem;
  font-weight: var(--gp-heading-weight); /* 800, never 700 */
  color: var(--gp-text);
}

.lede {
  margin: 0;
  font-size: 1.125rem; /* --text-lg */
  line-height: 1.556;
  color: var(--gp-text-muted);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1.25rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.grid > li {
  display: flex; /* so every panel takes the full row height */
}

.panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 1.5rem;
  background: var(--gp-bg);
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-panel);
  color: inherit;
  text-decoration: none;
}

/* Hover borrows Groupon's own secondary-control convention: the border darkens to
 * neutral-400, nothing moves and nothing lifts (§4 — the homepage barely uses
 * elevation). Focus is the same shape as the hit area, in brand green. */
.panel--link {
  cursor: pointer;
  transition: border-color var(--gp-duration) var(--gp-ease);
}
.panel--link:hover {
  border-color: var(--gp-text-decorative);
}
.panel--link:focus-visible {
  outline: 2px solid var(--gp-brand);
  outline-offset: 2px;
}

.meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.5rem;
}

.part {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--gp-text-muted);
}

/* Chips are Groupon's secondary button, unchanged — the site does not distinguish the
 * two (§5). Status is carried by the word, not by colour: none of these three states is
 * an error, and warning yellow fails contrast as text (§2). Green marks only the one
 * that is actually there to open. */
.chip {
  padding: 0.15em 0.6em;
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-pill);
  background: var(--gp-surface);
  font-size: 0.8125rem;
  font-weight: 700;
  line-height: 1.125rem;
  color: var(--gp-text);
}
.chip--live {
  background: var(--gp-brand-subtle);
  border-color: var(--gp-brand-subtle);
  color: var(--gp-discount-fg); /* green-700 on green-100 — 4.94:1, the §2 badge pair */
}

h2 {
  margin: 0 0 0.5rem;
  font-size: 1.25rem; /* --text-h3 */
  line-height: 1.5rem;
  font-weight: var(--gp-heading-weight);
  color: var(--gp-text);
}

.body {
  margin: 0 0 1.5rem;
  font-size: 1rem; /* --text-base. 15px would be off Groupon's scale entirely */
  line-height: 1.5rem;
  color: var(--gp-text-muted);
}

/* Primary button, measured off groupon.com: 38px tall, 13px/700, fully rounded (§5).
 * The only green on the page — green is commerce and action, never status. */
.btn {
  align-self: flex-start;
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  height: 38px;
  padding: 0 1.25rem;
  border: 1px solid var(--gp-brand);
  border-radius: var(--gp-radius-pill);
  background: var(--gp-brand);
  color: var(--gp-bg);
  font-size: 0.8125rem;
  font-weight: 700;
  transition: background var(--gp-duration) var(--gp-ease);
}
.panel--link:hover .btn {
  background: var(--gp-brand-hover);
  border-color: var(--gp-brand-hover);
}

/* Same 38px block as the button so the three panels line up on their last row. */
.pending {
  display: flex;
  align-items: center;
  height: 38px;
  margin-top: auto;
  font-size: 0.8125rem;
  color: var(--gp-text-muted);
}

.foot {
  max-width: 40rem;
  margin-top: 2.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--gp-separator);
  font-size: 0.875rem; /* --text-sm */
  line-height: 1.25rem;
  color: var(--gp-text-muted);
}
.foot p {
  margin: 0;
}
</style>
