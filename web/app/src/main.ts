import { createApp } from 'vue'

// Nunito Sans, self-hosted rather than pulled from Google's CDN — the deploy stays
// free of third-party requests. `--font-sans` names the family and nothing was loading
// it, so every heading rendered in the system fallback: extrabold headings are the
// single strongest Groupon cue (DESIGN-SYSTEM.md §3) and 800 needs the real face.
// The *static* package, not the variable one — the variable build registers itself as
// 'Nunito Sans Variable', which the generated token does not name. Weights: body 400,
// buttons and chips 700, headings 800. Latin-ext ships with each, so Polish diacritics
// resolve in the real face rather than a fallback (§9).
import '@fontsource/nunito-sans/400.css'
import '@fontsource/nunito-sans/700.css'
import '@fontsource/nunito-sans/800.css'

// Order matters: the generated Groupon tokens first, then the curated/invented
// layer that aliases onto them. Both files live in docs/design/ and are the same
// two files web/mock/build.py inlines — imported, never copied, so the mock and
// the app cannot drift. See 005-stack-init decision B.
import '@design/outputs/tokens.css'
import '@design/assets/prototype-theme.css'
import './style.css'

import App from './App.vue'

createApp(App).mount('#app')
