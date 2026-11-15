import type { ReactNode } from 'react'

import { useAsyncData } from '@/hooks/useAsyncData'

import { getHealth } from './api'
import { SystemStatusContext } from './context'

/**
 * Loads the health report once and shares it. The sidebar, the dashboard
 * and the chat screen all need it; without sharing each would send its own request.
 */
export function SystemStatusProvider({ children }: { children: ReactNode }) {
  const health = useAsyncData(getHealth)
  return <SystemStatusContext value={health}>{children}</SystemStatusContext>
}
