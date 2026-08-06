import { createApp } from 'vue'

// Order matters: the generated Groupon tokens first, then the curated/invented
// layer that aliases onto them. Both files live in docs/design/ and are the same
// two files web/mock/build.py inlines — imported, never copied, so the mock and
// the app cannot drift. See 005-stack-init decision B.
import '@design/outputs/tokens.css'
import '@design/assets/prototype-theme.css'
import './style.css'

import App from './App.vue'

createApp(App).mount('#app')
