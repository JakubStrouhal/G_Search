<script setup lang="ts">
// Orientation for a grader landing cold on /app#prototype. The chips below are
// grouped by internal vocabulary (render states); this strip is the plain-English
// key to them, and it says what the page IS before the page starts behaving.
//
// Number-free (006-one-page/SPEC.md G6): steps are marked by words, not figures,
// and no count or rate is quoted here — those live on the explainer, bound to
// story_data.json.
</script>

<template>
  <section class="howto" aria-label="How to use this prototype">
    <p class="what">
      <b>This is Part B of the case study — the working prototype.</b> It searches a real, hosted
      database seeded with the supplied catalogue. Nothing here is mocked; every search below runs
      against the same data the analysis on <a href="/">the explainer</a> was computed from.
    </p>
    <ul class="steps">
      <li><b>Click any chip below.</b> Each chip is a real logged query; it sets its own market and
        city and runs. Each row demonstrates one behaviour the analysis found — the failing rows are
        there on purpose, because what this does with no good answer is the point.</li>
      <li><b>Or search freely.</b> Pick a market and city at the top, then type what a customer
        would type — any language, typos included. A query outside the logged set is refused by
        name rather than guessed at; try one.</li>
      <li><b>Watch the panel on the right.</b> It narrates every search you run: the confidence
        band, the failure class from the analysis, and whether a demand row was just written to the
        database.</li>
    </ul>
  </section>
</template>

<style scoped>
.howto {
  margin: 1.25rem 0 0.25rem;
  padding: 1rem 1.25rem;
  background: var(--gp-bg);
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius, 0.5rem);
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.what {
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--gp-text);
}

.what a {
  color: inherit;
}

.steps {
  margin: 0;
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.steps li {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--gp-text-muted);
}

.steps li b {
  color: var(--gp-text);
}
</style>
