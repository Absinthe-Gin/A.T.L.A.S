import { Link } from 'react-router'

import { IconArrowRight } from '@/components/icons'
import { NOTE_INK } from '@/components/ui/noteColors'
import { StickyNote } from '@/components/ui/StickyNote'
import { cn } from '@/utils/cn'

import { type AppModule, MODULES } from '../catalog'

// Hand-placed look: each note sits at its own small angle, the same every visit.
// Kept within about ±1°: enough to look hand-placed, small enough to read comfortably.
const TILTS = [-1, 0.8, -0.4, 1, -0.7]

function ModuleNote({ module, tilt }: { module: AppModule; tilt: number }) {
  const available = module.status === 'available'

  return (
    <StickyNote color={module.note} tilt={tilt} interactive className="h-full">
      {/* The whole note is one link; the stretched pseudo-element makes it clickable everywhere. */}
      <div className="flex h-full flex-col p-5 pt-6">
        <div className="flex items-start justify-between gap-3">
          <span
            className={cn(
              'flex size-10 items-center justify-center rounded-full bg-surface/70 shadow-raise',
              NOTE_INK[module.note],
            )}
          >
            {module.renderIcon(20)}
          </span>
          <span
            className={cn(
              'rounded-full px-2.5 py-0.5 text-xs font-semibold',
              available ? 'bg-success-soft text-success' : 'bg-surface/60 text-fg-muted',
            )}
          >
            {available ? 'Đang hoạt động' : 'Sắp có'}
          </span>
        </div>

        <h3 className="mt-4 text-lg font-extrabold text-fg">
          <Link
            to={module.path}
            className="rounded-control outline-none after:absolute after:inset-0 after:rounded-note focus-visible:after:outline-2 focus-visible:after:outline-offset-2 focus-visible:after:outline-ring"
          >
            {module.label}
          </Link>
        </h3>
        <p className="mt-1 flex-1 text-sm text-fg-muted text-pretty">{module.summary}</p>

        <span className={cn('mt-4 inline-flex items-center gap-1 text-sm font-semibold', NOTE_INK[module.note])}>
          {available ? 'Mở' : 'Xem dự kiến'}
          <IconArrowRight size={16} />
        </span>
      </div>
    </StickyNote>
  )
}

/** Every module as a sticky note in its own colour. */
export function ModuleNotes() {
  const modules = MODULES.filter((module) => module.id !== 'dashboard')

  return (
    <ul className="grid gap-x-5 gap-y-7 pt-2 sm:grid-cols-2 xl:grid-cols-3">
      {modules.map((module, index) => (
        <li key={module.id}>
          <ModuleNote module={module} tilt={TILTS[index % TILTS.length] ?? 0} />
        </li>
      ))}
    </ul>
  )
}
