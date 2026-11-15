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

/** Compact status line for the sidebar. */
export function SystemStatusIndicator() {
  const health = useSystemStatus()
  const summary = summarize(health)

  return (
    <div role="status" className="flex min-w-0 items-center gap-2.5 text-xs">
      <span
        aria-hidden="true"
        className={`size-2 shrink-0 rounded-full transition-colors duration-300 ${DOT_TONES[summary.tone]}`}
      />
      <span className="truncate text-fg-muted">{summary.label}</span>
    </div>
  )
}
