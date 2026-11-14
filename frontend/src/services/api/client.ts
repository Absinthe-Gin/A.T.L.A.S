import axios, { type AxiosAdapter, type AxiosInstance } from 'axios'

import { env } from '@/config/env'

import { toApiError } from './errors'

const DEFAULT_TIMEOUT_MS = 15_000

interface ApiClientOptions {
  baseURL: string
  timeoutMs?: number
  /** Replaces the network layer. Used by tests. */
  adapter?: AxiosAdapter
}

/** Build an HTTP client whose failures are always `ApiError`. */
export function createApiClient(options: ApiClientOptions): AxiosInstance {
  const client = axios.create({
    baseURL: options.baseURL,
    timeout: options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
    headers: { Accept: 'application/json' },
    adapter: options.adapter,
  })

  client.interceptors.response.use(
    (response) => response,
    (error: unknown) => Promise.reject(toApiError(error)),
  )

  return client
}

/** The application-wide client. Feature `api.ts` files are its only callers. */
export const apiClient = createApiClient({ baseURL: env.apiBaseUrl })
