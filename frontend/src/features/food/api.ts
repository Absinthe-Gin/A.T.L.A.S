import { apiClient } from '@/services/api/client'

import type { DishSearchResult, RegionRecommendation } from './types'

export async function getRecommendation(
  lat: number,
  lon: number,
  signal?: AbortSignal,
): Promise<RegionRecommendation> {
  const response = await apiClient.get<RegionRecommendation>('/food/recommendations', {
    params: { lat, lon },
    signal,
  })
  return response.data
}

export interface RestaurantQuery {
  dish: string
  lat: number
  lon: number
  radiusM: number
  limit?: number
}

export async function findRestaurants(query: RestaurantQuery, signal?: AbortSignal): Promise<DishSearchResult> {
  const response = await apiClient.get<DishSearchResult>('/food/restaurants', {
    params: {
      dish: query.dish,
      lat: query.lat,
      lon: query.lon,
      radius_m: query.radiusM,
      limit: query.limit ?? 10,
    },
    signal,
  })
  return response.data
}
