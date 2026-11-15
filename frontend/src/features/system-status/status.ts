import type { BadgeTone } from '@/components/ui/Badge'
import type { AsyncData } from '@/hooks/useAsyncData'

import type { HealthResponse } from './types'

export interface StatusSummary {
  tone: BadgeTone
  label: string
}

/** One-line summary of the whole system, for compact displays. */
export function summarize(health: AsyncData<HealthResponse>): StatusSummary {
  if (health.status === 'loading') return { tone: 'neutral', label: 'Đang kiểm tra' }
  if (health.status === 'error') return { tone: 'danger', label: 'Mất kết nối Backend' }
  if (health.data.status !== 'ok') return { tone: 'danger', label: 'Hệ thống gặp sự cố' }
  if (health.data.checks.llm.status !== 'ok') return { tone: 'warning', label: 'AI chưa sẵn sàng' }
  return { tone: 'success', label: 'Hoạt động bình thường' }
}

/** Whether the chat can be expected to answer. `null` while unknown. */
export function isAiReady(health: AsyncData<HealthResponse>): boolean | null {
  if (health.status !== 'success') return null
  return health.data.checks.llm.status === 'ok'
}
