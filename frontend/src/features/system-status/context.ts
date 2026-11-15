import { createContext, useContext } from 'react'

import type { AsyncData } from '@/hooks/useAsyncData'

import type { HealthResponse } from './types'

export const SystemStatusContext = createContext<AsyncData<HealthResponse> | null>(null)

/** The latest health report, shared by every screen that shows system status. */
export function useSystemStatus(): AsyncData<HealthResponse> {
  const value = useContext(SystemStatusContext)
  if (value === null) {
    throw new Error('useSystemStatus must be used inside <SystemStatusProvider>.')
  }
  return value
}
