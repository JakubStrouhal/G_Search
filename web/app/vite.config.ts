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
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@design': fileURLToPath(new URL('../../docs/design', import.meta.url)),
    },
  },
  server: {
    // Honour PORT when the harness assigns one; 5173 otherwise.
    port: Number(process.env.PORT) || 5173,
    fs: { allow: [repoRoot] },
  },
})
