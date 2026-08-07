<script setup lang="ts">
// Sign-out for the deployment's access gate (middleware.ts).
//
// A plain form POST, no fetch and no client state, because there is no client state to
// clear: the gate cookie is HttpOnly, so document.cookie cannot see it and cannot remove
// it. Only the server that set it can unset it. The route answers from anywhere on the
// origin — including /explainer.html, which is a static file this component never
// renders into — so the URL is the general mechanism and the button is one caller of it.
//
// Design: DESIGN-SYSTEM.md §5 secondary button, measured off groupon.com — 32px,
// 12px/700, rounded-full, #edeff2 filling to white on hover with the border darkening to
// neutral-400. Deliberately not the primary: §2 keeps green for the one real action on a
// page, and on the front door that is already the explainer CTA. Leaving a session is
// not the thing a reader came here to do.

// The gate is Vercel middleware; `npm run dev` serves the app with no middleware in front
// of it, where POSTing this route would 404. Rendering it only in a production build
// keeps a control that cannot work off the screen it cannot work on.
const gated = import.meta.env.PROD

const LOGOUT_PATH = '/__gate/logout'
</script>

<template>
  <form v-if="gated" class="signout" :action="LOGOUT_PATH" method="post">
    <button type="submit">Sign out</button>
  </form>
</template>

<style scoped>
/* Fixed rather than a header row: SiteIndex is sized so everything through the footer
 * fits a 14" laptop without scrolling, and a new band at the top would cost that. */
.signout {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 10;
  margin: 0;
}

button {
  height: 32px;
  padding: 0 1rem;
  border: 1px solid var(--gp-separator);
  border-radius: var(--gp-radius-pill);
  background: var(--gp-surface);
  color: var(--gp-text);
  font-family: inherit;
  font-size: 0.75rem; /* 12px/700 — §5's secondary, one step under the 13px primary */
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  transition:
    background var(--gp-duration) var(--gp-ease),
    border-color var(--gp-duration) var(--gp-ease);
}

button:hover {
  background: var(--gp-bg);
  border-color: var(--gp-text-decorative);
}

button:focus-visible {
  outline: 2px solid var(--gp-brand);
  outline-offset: 2px;
}

@media print {
  .signout {
    display: none;
  }
}
</style>
