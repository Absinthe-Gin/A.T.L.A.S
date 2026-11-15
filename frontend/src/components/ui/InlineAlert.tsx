import type { ReactNode } from 'react'

import { IconAlert } from '@/components/icons'
import { cn } from '@/utils/cn'

type AlertTone = 'danger' | 'warning'

const TONES: Record<AlertTone, string> = {
  danger: 'border-danger/30 bg-danger-soft',
  warning: 'border-warning/30 bg-warning-soft',
}

const ICON_TONES: Record<AlertTone, string> = {
  danger: 'text-danger',
  warning: 'text-warning',
}

interface InlineAlertProps {
  tone?: AlertTone
  title: string
  children?: ReactNode
  /** Request ID from the API error, shown so the user can report it. */
  requestId?: string | null
  action?: ReactNode
  className?: string
}

export function InlineAlert({
  tone = 'danger',
  title,
  children,
  requestId,
  action,
  className,
}: InlineAlertProps) {
  return (
    <div
      // Errors interrupt; warnings are announced politely.
      role={tone === 'danger' ? 'alert' : 'status'}
      className={cn('flex animate-rise gap-3 rounded-control border p-3 text-sm', TONES[tone], className)}
    >
      <IconAlert size={18} className={cn('mt-0.5 shrink-0', ICON_TONES[tone])} />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-medium text-fg">{title}</p>
        {children && <div className="text-fg-muted">{children}</div>}
        {requestId && (
          <p className="font-mono text-xs text-fg-subtle">
            Mã yêu cầu: <span className="select-all">{requestId}</span>
          </p>
        )}
        {action && <div className="pt-1">{action}</div>}
      </div>
    </div>
  )
}
