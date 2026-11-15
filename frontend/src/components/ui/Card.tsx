import type { ComponentProps } from 'react'

import { cn } from '@/utils/cn'

export function Card({ className, ...props }: ComponentProps<'section'>) {
  return <section className={cn('rounded-card border border-border bg-surface', className)} {...props} />
}
