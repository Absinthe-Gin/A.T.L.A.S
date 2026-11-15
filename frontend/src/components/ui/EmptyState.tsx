import type { ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description?: ReactNode
  action?: ReactNode
  children?: ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, children, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center px-6 py-10 text-center', className)}>
      <div className="mb-4 flex size-12 items-center justify-center rounded-card border border-border bg-surface-2 text-fg-muted">
        {icon}
      </div>
      <h2 className="text-base font-semibold text-fg">{title}</h2>
      {description && <p className="mt-1.5 max-w-md text-sm text-fg-muted">{description}</p>}
      {children && <div className="mt-5 w-full max-w-md">{children}</div>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
