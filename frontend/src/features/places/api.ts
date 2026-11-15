import { apiClient } from '@/services/api/client'

import type { GeoPlace } from './types'

export async function searchPlaces(query: string, signal?: AbortSignal): Promise<GeoPlace[]> {
  const response = await apiClient.get<GeoPlace[]>('/places/search', {
    params: { q: query, limit: 6 },
    signal,
  })
  return response.data
}
