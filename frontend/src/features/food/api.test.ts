import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient } from '@/services/api/client'

import { findRestaurants, getRecommendation } from './api'

describe('food api', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: 'body' })
  })

  it('asks for the regional recommendation by coordinates', async () => {
    const controller = new AbortController()

    await expect(getRecommendation(16.05, 108.2, controller.signal)).resolves.toBe('body')

    expect(apiClient.get).toHaveBeenCalledWith('/food/recommendations', {
      params: { lat: 16.05, lon: 108.2 },
      signal: controller.signal,
    })
  })

  it('sends the dish, origin and radius as query parameters, with a default limit', async () => {
    await findRestaurants({ dish: 'bún bò', lat: 16.05, lon: 108.2, radiusM: 3000 })

    expect(apiClient.get).toHaveBeenCalledWith('/food/restaurants', {
      params: { dish: 'bún bò', lat: 16.05, lon: 108.2, radius_m: 3000, limit: 10 },
      signal: undefined,
    })
  })
})
