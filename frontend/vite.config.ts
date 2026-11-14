import { fileURLToPath } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    // Tests must not depend on a developer's local `.env`.
    env: { VITE_API_BASE_URL: 'http://api.test/api/v1' },
    setupFiles: ['./src/test/setup.ts'],
    // Tests assert on behaviour, not styling.
    css: false,
  },
})
