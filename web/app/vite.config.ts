import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// The design tokens live outside this app, in docs/design/, because web/mock/build.py
// inlines the same two files. One source, two consumers — see 005-stack-init decision B.
// The alias plus the fs.allow entry are what let Vite read across the repo boundary.
const repoRoot = fileURLToPath(new URL('../..', import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    // The landing page is the Part A explainer, copied into public/index.html by
    // scripts/copy-explainer.mjs. So this app is NOT the root document — its entry is
    // app.html, and Vercel rewrites /app onto it. Without this input override Vite
    // looks for index.html at the project root and would fight the copied file for it.
    rollupOptions: { input: fileURLToPath(new URL('./app.html', import.meta.url)) },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@design': fileURLToPath(new URL('../../docs/design', import.meta.url)),
      // The chips fixture (010-screens task 02) lives outside web/app/, same
      // reason as @design: one generated file, read by the app and nowhere
      // hand-typed. Declared in BOTH this file and tsconfig.app.json — the
      // @design alias is the precedent for what happens if only one is edited.
      '@fixtures': fileURLToPath(new URL('../../docs/analysis/010-screens/outputs', import.meta.url)),
    },
  },
  server: {
    // Honour PORT when the harness assigns one; 5173 otherwise.
    port: Number(process.env.PORT) || 5173,
    fs: { allow: [repoRoot] },
  },
})
