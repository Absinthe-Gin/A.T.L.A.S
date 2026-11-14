import { fileURLToPath } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

// 5710 instead of Vite's default 5173, so this project does not collide with
// other projects on the same machine. Override with VITE_DEV_SERVER_PORT.
const DEFAULT_DEV_SERVER_PORT = 5710

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const port = Number(env.VITE_DEV_SERVER_PORT) || DEFAULT_DEV_SERVER_PORT

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    // Fail instead of silently moving to another port: the backend allows
    // only the configured origin (CORS_ALLOWED_ORIGINS).
    server: { port, strictPort: true },
    preview: { port, strictPort: true },
    test: {
      environment: 'jsdom',
      // Tests must not depend on a developer's local `.env`.
      env: { VITE_API_BASE_URL: 'http://api.test/api/v1' },
      setupFiles: ['./src/test/setup.ts'],
      // Tests assert on behaviour, not styling.
      css: false,
    },
  }
})
