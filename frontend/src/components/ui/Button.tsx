import type { ComponentProps, ReactNode } from 'react'

import { cn } from '@/utils/cn'

import { type ButtonSize, type ButtonVariant, buttonClasses } from './buttonClasses'
import { Spinner } from './Spinner'

interface ButtonProps extends ComponentProps<'button'> {
  variant?: ButtonVariant
  size?: ButtonSize
  /** Shows a spinner, disables the button and announces the busy state. */
  loading?: boolean
  icon?: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  disabled,
  className,
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(buttonClasses(variant, size), className)}
      {...props}
    >
      {loading ? <Spinner size={16} /> : icon}
      {children}
    </button>
  )
}
