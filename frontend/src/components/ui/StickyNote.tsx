import type { ComponentProps, CSSProperties } from 'react'

import { cn } from '@/utils/cn'

import { NOTE_PAPER, type StickyNoteColor } from './noteColors'

interface StickyNoteProps extends ComponentProps<'div'> {
  color?: StickyNoteColor
  /** Tilt in degrees. Small values (±2°) look hand-placed; 0 for a straight note. */
  tilt?: number
  /** Straighten and lift on hover: for notes that are links or buttons. */
  interactive?: boolean
  /** Two strips at the top corners instead of one in the middle. */
  tape?: 'center' | 'corners' | 'none'
}

/** A note taped to the page. Purely presentational; put content and links inside. */
export function StickyNote({
  color = 'yellow',
  tilt = 0,
  interactive = false,
  tape = 'center',
  className,
  style,
  children,
  ...props
}: StickyNoteProps) {
  return (
    <div
      className={cn(
        'relative rounded-note shadow-lift',
        'rotate-(--tilt) transition-[rotate,translate,box-shadow] duration-200 ease-out',
        interactive && 'hover:-translate-y-0.5 hover:rotate-0 focus-within:-translate-y-0.5 focus-within:rotate-0',
        NOTE_PAPER[color],
        className,
      )}
      style={{ '--tilt': `${tilt}deg`, ...style } as CSSProperties}
      {...props}
    >
      {tape === 'center' && (
        <span aria-hidden="true" className="absolute -top-2.5 left-1/2 h-5 w-16 -translate-x-1/2 -rotate-2 bg-tape" />
      )}
      {tape === 'corners' && (
        <>
          <span aria-hidden="true" className="absolute -top-2 -left-3 h-5 w-14 -rotate-[30deg] bg-tape" />
          <span aria-hidden="true" className="absolute -top-2 -right-3 h-5 w-14 rotate-[30deg] bg-tape" />
        </>
      )}
      {children}
    </div>
  )
}
