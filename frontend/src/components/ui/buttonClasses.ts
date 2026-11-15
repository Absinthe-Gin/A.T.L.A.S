import { cn } from '@/utils/cn'

/** Classes of `Button`, also used to style links that look like buttons. */
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md'

const BASE =
  'inline-flex shrink-0 cursor-pointer select-none items-center justify-center gap-2 rounded-control font-semibold ' +
  'transition-[background-color,border-color,color,box-shadow,translate] duration-150 ease-out ' +
  // Pressing sinks the button by a pixel and drops its shadow: the click is felt.
  'active:translate-y-px active:shadow-none ' +
  // Disabled reads as unavailable, not as a faded version of the action colour.
  'disabled:cursor-not-allowed disabled:translate-y-0 disabled:shadow-none'

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'btn-action text-action-fg disabled:bg-surface-2 disabled:text-fg-subtle',
  secondary:
    'border border-border-strong bg-surface text-fg shadow-raise hover:border-primary/40 hover:bg-surface-2 ' +
    'disabled:border-border disabled:bg-surface-2 disabled:text-fg-subtle',
  ghost: 'text-fg-muted hover:bg-fg/5 hover:text-fg disabled:text-fg-subtle disabled:hover:bg-transparent',
  danger:
    'border border-danger/50 bg-surface text-danger shadow-raise hover:bg-danger-soft ' +
    'disabled:border-border disabled:text-fg-subtle',
}

const SIZES: Record<ButtonSize, string> = {
  // Both sizes keep a 40px+ hit area; `md` meets the 44px touch target.
  sm: 'min-h-10 px-4 text-sm',
  md: 'min-h-11 px-5 text-[0.9375rem]',
}

export function buttonClasses(variant: ButtonVariant = 'primary', size: ButtonSize = 'md') {
  return cn(BASE, VARIANTS[variant], SIZES[size])
}
