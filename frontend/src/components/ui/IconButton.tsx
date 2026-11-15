import type { ComponentProps, ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface IconButtonProps extends Omit<ComponentProps<'button'>, 'children' | 'aria-label'> {
  /** Accessible name. Required because the button shows only an icon. */
  label: string
  icon: ReactNode
  variant?: 'ghost' | 'secondary'
}

export function IconButton({
  label,
  icon,
  variant = 'ghost',
  className,
  type = 'button',
  ...props
}: IconButtonProps) {
  return (
    <button
      type={type}
      aria-label={label}
      title={label}
      className={cn(
        'inline-flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-control',
        'transition-[background-color,border-color,color,translate] duration-150 ease-out active:translate-y-px',
        'disabled:cursor-not-allowed disabled:translate-y-0 disabled:text-fg-subtle',
        variant === 'ghost'
          ? 'text-fg-muted hover:bg-surface-2 hover:text-fg disabled:hover:bg-transparent'
          : 'border border-border-strong bg-surface text-fg shadow-raise hover:bg-surface-2',
        className,
      )}
      {...props}
    >
      {icon}
    </button>
  )
}
