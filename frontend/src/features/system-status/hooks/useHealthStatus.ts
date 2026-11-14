import { type AsyncData, useAsyncData } from '@/hooks/useAsyncData'

import { getHealth } from '../api'
import type { HealthResponse } from '../types'

export function useHealthStatus(): AsyncData<HealthResponse> {
  return useAsyncData(getHealth)
}
