import { NavLink } from 'react-router'

import { NOTE_INK } from '@/components/ui/noteColors'
import { MODULES } from '@/features/modules/catalog'
import { cn } from '@/utils/cn'

interface NavigationProps {
  /** Called after a link is chosen, e.g. to close the mobile menu. */
  onNavigate?: () => void
  /** Icons only, centred in the column. The label stays available to screen readers and as a tooltip. */
  collapsed?: boolean
}

export function Navigation({ onNavigate, collapsed = false }: NavigationProps) {
  return (
    <ul className="space-y-0.5">
      {MODULES.map((module) => (
        <li key={module.id}>
          <NavLink
            to={module.path}
            // The dashboard lives at "/", which every path starts with.
            end={module.path === '/'}
            onClick={onNavigate}
            title={collapsed ? module.label : undefined}
            className={({ isActive }) =>
              cn(
                'group flex min-h-10 items-center rounded-control text-sm',
                collapsed ? 'justify-center px-0' : 'gap-3 px-3',
                'transition-[background-color,color,box-shadow] duration-150 ease-out',
                // The current page is a sheet of paper lifted off the notebook margin.
                isActive
                  ? 'bg-surface font-semibold text-fg shadow-raise'
                  : 'text-fg-muted hover:bg-fg/5 hover:text-fg',
              )
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={cn(
                    'shrink-0 transition-colors duration-150',
                    // The current page shows its module colour, as on its sticky note.
                    isActive ? NOTE_INK[module.note] : 'text-fg-subtle group-hover:text-fg-muted',
                  )}
                >
                  {module.renderIcon(18)}
                </span>
                {collapsed ? (
                  <span className="sr-only">{module.label}</span>
                ) : (
                  <>
                    <span className="flex-1 truncate">{module.label}</span>
                    {module.status === 'planned' && (
                      <span className="text-xs font-normal text-fg-subtle">Sắp có</span>
                    )}
                  </>
                )}
              </>
            )}
          </NavLink>
        </li>
      ))}
    </ul>
  )
}
