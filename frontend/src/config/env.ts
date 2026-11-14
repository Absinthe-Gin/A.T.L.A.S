/**
 * The only place that reads environment variables.
 * Fails at startup with a clear message when configuration is missing.
 */

export interface AppEnv {
  apiBaseUrl: string
}

export function readEnv(source: ImportMetaEnv): AppEnv {
  const apiBaseUrl = source.VITE_API_BASE_URL?.trim()
  if (!apiBaseUrl) {
    throw new Error(
      'Missing VITE_API_BASE_URL. Copy frontend/.env.example to frontend/.env and set it.',
    )
  }
  return { apiBaseUrl: apiBaseUrl.replace(/\/+$/, '') }
}

export const env: AppEnv = readEnv(import.meta.env)
