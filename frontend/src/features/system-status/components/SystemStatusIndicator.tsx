import { useSystemStatus } from '../context'
import { summarize } from '../status'

const DOT_TONES = {
  neutral: 'bg-fg-subtle',
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
  primary: 'bg-primary',
  accent: 'bg-accent',
} as const

interface SystemStatusIndicatorProps {
  /** Only the coloured dot, centred; the label is kept for screen readers and as a tooltip. */
  compact?: boolean
}

/** Compact status line for the sidebar. */
export function SystemStatusIndicator({ compact = false }: SystemStatusIndicatorProps) {
  const health = useSystemStatus()
  const summary = summarize(health)
  const dot = (
    <span
      aria-hidden="true"
      className={`size-2 shrink-0 rounded-full transition-colors duration-300 ${DOT_TONES[summary.tone]}`}
    />
  )

  if (compact) {
    return (
      <div role="status" title={summary.label} className="flex items-center justify-center">
        {dot}
        <span className="sr-only">{summary.label}</span>
      </div>
    )
  }

  return (
    <div role="status" className="flex min-w-0 items-center gap-2.5 text-xs">
      {dot}
      <span className="truncate text-fg-muted">{summary.label}</span>
    </div>
  )
}
