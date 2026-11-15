import { useState } from 'react'

import { Button } from '@/components/ui/Button'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'
import { cn } from '@/utils/cn'

import type { PendingAction } from '../types'

const OUTCOME: Record<Exclude<PendingAction['status'], 'pending'>, { text: string; className: string }> = {
  confirmed: { text: 'Đã lưu.', className: 'bg-success-soft text-success' },
  cancelled: { text: 'Đã hủy, không có gì thay đổi.', className: 'bg-surface-2 text-fg-muted' },
  failed: { text: 'Không thực hiện được.', className: 'bg-danger-soft text-danger' },
}

interface PendingActionCardProps {
  action: PendingAction
  onResolve: (id: string, decision: 'confirm' | 'cancel') => Promise<ApiError | null>
}

/** A change Atlas proposed. Nothing is saved until the user presses "Xác nhận". */
export function PendingActionCard({ action, onResolve }: PendingActionCardProps) {
  const [busy, setBusy] = useState<'confirm' | 'cancel' | null>(null)
  const [error, setError] = useState<ApiError | null>(null)

  const resolve = async (decision: 'confirm' | 'cancel') => {
    setBusy(decision)
    setError(null)
    setError(await onResolve(action.id, decision))
    setBusy(null)
  }

  return (
    <div className="ml-8 max-w-md animate-rise rounded-card border border-border-strong bg-surface p-4 shadow-raise">
      <p className="text-xs font-semibold text-primary">Đề xuất thay đổi</p>
      <p className="mt-1 text-[0.9375rem] text-fg">{action.summary}</p>

      {action.status === 'pending' ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <Button size="sm" loading={busy === 'confirm'} disabled={busy !== null} onClick={() => void resolve('confirm')}>
            Xác nhận
          </Button>
          <Button
            size="sm"
            variant="secondary"
            loading={busy === 'cancel'}
            disabled={busy !== null}
            onClick={() => void resolve('cancel')}
          >
            Hủy
          </Button>
        </div>
      ) : (
        <p
          role="status"
          className={cn('mt-3 inline-block rounded-full px-3 py-1 text-xs font-semibold', OUTCOME[action.status].className)}
        >
          {OUTCOME[action.status].text}
          {action.status === 'failed' && action.error_message ? ` ${action.error_message}` : ''}
        </p>
      )}

      {error && (
        <InlineAlert className="mt-3" title="Chưa xử lý được đề xuất" requestId={error.requestId}>
          {error.message}
        </InlineAlert>
      )}
    </div>
  )
}
