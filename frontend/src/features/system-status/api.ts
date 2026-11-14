import { apiClient } from '@/services/api/client'

import type { HealthResponse } from './types'

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health', {
    signal,
    // A degraded backend answers 503 with the same body; that is a result, not a failure.
    validateStatus: (status) => status === 200 || status === 503,
  })
  return response.data
}
