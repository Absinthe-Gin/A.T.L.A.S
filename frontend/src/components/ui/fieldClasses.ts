import { cn } from '@/utils/cn'

/** Text inputs, selects and date inputs share one look. */
export function fieldClasses(invalid = false): string {
  return cn(
    'min-h-11 w-full rounded-control border bg-surface px-3 text-[0.9375rem] text-fg shadow-raise',
    'transition-[border-color,box-shadow] duration-150 ease-out placeholder:text-fg-subtle',
    'focus-visible:outline-none focus-visible:border-primary/60 focus-visible:shadow-[0_0_0_3px_var(--primary-soft)]',
    'disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-fg-subtle',
    invalid ? 'border-danger' : 'border-border-strong',
  )
}

export const labelClasses = 'mb-1.5 block text-sm font-semibold text-fg'
export const hintClasses = 'mt-1.5 text-xs text-fg-subtle'
export const errorClasses = 'mt-1.5 text-xs font-medium text-danger'
