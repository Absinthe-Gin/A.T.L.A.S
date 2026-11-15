import { useCallback } from 'react'

import { type AsyncData, useAsyncData } from '@/hooks/useAsyncData'

import { getRecommendation } from '../api'
import type { RegionRecommendation } from '../types'

/** Specialties of the region nearest to `point`. Reloads whenever the point changes. */
export function useRecommendation(point: { lat: number; lon: number }): AsyncData<RegionRecommendation> {
  const { lat, lon } = point
  const fetcher = useCallback((signal: AbortSignal) => getRecommendation(lat, lon, signal), [lat, lon])
  return useAsyncData(fetcher)
}
