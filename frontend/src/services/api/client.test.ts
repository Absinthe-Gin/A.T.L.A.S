import { type AxiosAdapter, AxiosError, type AxiosResponse } from 'axios'
import { describe, expect, it } from 'vitest'

import { createApiClient } from './client'
import { ApiError } from './errors'

/** Network layer stand-in that answers every request with a fixed response. */
function respondWith(status: number, data: unknown): AxiosAdapter {
  return async (config) => {
    const response: AxiosResponse = { status, data, headers: {}, statusText: '', config }
    const validateStatus = config.validateStatus ?? ((code: number) => code >= 200 && code < 300)
    if (validateStatus(status)) {
      return response
    }
    throw new AxiosError('Request failed', 'ERR_BAD_RESPONSE', config, null, response)
  }
}

describe('createApiClient', () => {
  it('sends requests to the configured base URL', async () => {
    let requestedUrl = ''
    const client = createApiClient({
      baseURL: 'http://api.test/api/v1',
      adapter: async (config) => {
        requestedUrl = `${config.baseURL}${config.url}`
        return { status: 200, data: { ok: true }, headers: {}, statusText: 'OK', config }
      },
    })

    const response = await client.get('/health')

    expect(requestedUrl).toBe('http://api.test/api/v1/health')
    expect(response.data).toEqual({ ok: true })
  })

  it('rejects failed requests with an ApiError', async () => {
    const client = createApiClient({
      baseURL: 'http://api.test',
      adapter: respondWith(404, {
        error: { code: 'not_found', message: 'Không có', details: [], request_id: 'r1' },
      }),
    })

    const failure = await client.get('/missing').catch((error: unknown) => error)

    expect(failure).toBeInstanceOf(ApiError)
    expect(failure).toMatchObject({ kind: 'not_found', status: 404, requestId: 'r1' })
  })

  it('rejects network failures with an ApiError', async () => {
    const client = createApiClient({
      baseURL: 'http://api.test',
      adapter: async (config) => {
        throw new AxiosError('Network Error', 'ERR_NETWORK', config)
      },
    })

    await expect(client.get('/health')).rejects.toMatchObject({ kind: 'network' })
  })

  it('applies the configured timeout', () => {
    const client = createApiClient({ baseURL: 'http://api.test', timeoutMs: 1234 })

    expect(client.defaults.timeout).toBe(1234)
  })
})
