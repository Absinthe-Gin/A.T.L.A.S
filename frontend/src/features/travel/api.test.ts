import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient } from '@/services/api/client'

import { addItem, createPlan, deletePlan, getTransport, getWeather, listPlans } from './api'
import { searchPlaces } from '@/features/places'

describe('travel api', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: 'body' })
    vi.spyOn(apiClient, 'post').mockResolvedValue({ data: 'created' })
    vi.spyOn(apiClient, 'delete').mockResolvedValue({ data: undefined })
  })

  it('lists plans and forwards the abort signal', async () => {
    const controller = new AbortController()
    await expect(listPlans(controller.signal)).resolves.toBe('body')
    expect(apiClient.get).toHaveBeenCalledWith('/travel/plans', { params: { limit: 100 }, signal: controller.signal })
  })

  it('creates a plan and adds an item', async () => {
    const plan = { title: 'Đà Lạt', destination: null, start_date: null, end_date: null, note: null }
    await expect(createPlan(plan)).resolves.toBe('created')
    expect(apiClient.post).toHaveBeenCalledWith('/travel/plans', plan)

    const item = { title: 'Chợ', day: null, start_time: null, place: null, note: null }
    await addItem('p1', item)
    expect(apiClient.post).toHaveBeenCalledWith('/travel/plans/p1/items', item)
  })

  it('deletes a plan', async () => {
    await deletePlan('p1')
    expect(apiClient.delete).toHaveBeenCalledWith('/travel/plans/p1')
  })

  it('searches places and asks for weather by coordinates', async () => {
    await searchPlaces('Huế')
    expect(apiClient.get).toHaveBeenCalledWith('/places/search', { params: { q: 'Huế', limit: 6 }, signal: undefined })

    await getWeather(11.9, 108.4)
    expect(apiClient.get).toHaveBeenCalledWith('/travel/weather', {
      params: { lat: 11.9, lon: 108.4, days: 7 },
      signal: undefined,
    })
  })

  it('sends both ends of the trip as flat query parameters', async () => {
    await getTransport({
      origin: { name: 'Hà Nội', lat: 21, lon: 105.8 },
      destination: { name: 'Đà Lạt', lat: 11.9, lon: 108.4 },
      travel_date: '2026-12-01',
      adults: 2,
    })
    expect(apiClient.get).toHaveBeenCalledWith('/travel/transport', {
      params: {
        origin_name: 'Hà Nội',
        origin_lat: 21,
        origin_lon: 105.8,
        destination_name: 'Đà Lạt',
        destination_lat: 11.9,
        destination_lon: 108.4,
        travel_date: '2026-12-01',
        adults: 2,
      },
      signal: undefined,
    })
  })
})
