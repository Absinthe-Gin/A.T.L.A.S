import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient } from '@/services/api/client'

import { getHealth } from './api'
import type { HealthResponse } from './types'

const body: HealthResponse = {
  status: 'degraded',
  environment: 'testing',
  version: '0.1.0',
  checks: { database: 'error' },
}

describe('getHealth', () => {
  beforeEach(() => {
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: body })
  })

  it('requests the health endpoint and returns the response body', async () => {
    await expect(getHealth()).resolves.toEqual(body)

    expect(apiClient.get).toHaveBeenCalledWith('/health', expect.anything())
  })

  it('treats 503 as a result so a degraded backend can be displayed', async () => {
    await getHealth()

    const options = vi.mocked(apiClient.get).mock.calls[0]?.[1]
    expect(options?.validateStatus?.(200)).toBe(true)
    expect(options?.validateStatus?.(503)).toBe(true)
    expect(options?.validateStatus?.(500)).toBe(false)
  })

  it('forwards the abort signal', async () => {
    const controller = new AbortController()

    await getHealth(controller.signal)

    expect(vi.mocked(apiClient.get).mock.calls[0]?.[1]?.signal).toBe(controller.signal)
  })
})
