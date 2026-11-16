import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router'

import { IconClose, IconMenu, IconSidebar } from '@/components/icons'
import { IconButton } from '@/components/ui/IconButton'
import { SystemStatusIndicator } from '@/features/system-status/components/SystemStatusIndicator'
import { SystemStatusProvider } from '@/features/system-status/SystemStatusProvider'
import { useSidebarCollapsed } from '@/hooks/useSidebarCollapsed'
import { cn } from '@/utils/cn'

import { BrandMark } from './BrandMark'
import { Navigation } from './Navigation'
import { ThemeToggle } from './ThemeToggle'

const MOBILE_NAV_ID = 'mobile-navigation'

function SidebarFooter({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={cn(
        'flex items-center border-t border-border py-3',
        // Folded: the status dot and the theme button stack in the centre of the column.
        compact ? 'flex-col gap-3 px-0' : 'gap-2 px-4',
      )}
    >
      <div className={cn('min-w-0', !compact && 'flex-1')}>
        <SystemStatusIndicator compact={compact} />
      </div>
      <ThemeToggle />
    </div>
  )
}

export function AppLayout() {
  const { pathname } = useLocation()
  // The menu remembers the page it was opened on, so it closes by itself on
  // any route change, including back/forward.
  const [openOnPath, setOpenOnPath] = useState<string | null>(null)
  const menuOpen = openOnPath === pathname
  const closeMenu = () => setOpenOnPath(null)
  const [collapsed, toggleCollapsed] = useSidebarCollapsed()

  useEffect(() => {
    if (!menuOpen) return
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpenOnPath(null)
    }
    document.addEventListener('keydown', closeOnEscape)
    return () => document.removeEventListener('keydown', closeOnEscape)
  }, [menuOpen])

  return (
    <SystemStatusProvider>
      <div
        className={cn(
          'min-h-dvh bg-bg text-fg lg:grid',
          // The column eases between its two widths; the page reflows with it.
          'lg:transition-[grid-template-columns] lg:duration-250 lg:ease-out',
          collapsed ? 'lg:grid-cols-[4.5rem_1fr]' : 'lg:grid-cols-[15.5rem_1fr]',
        )}
      >
        <a
          href="#main"
          className="sr-only rounded-control bg-action px-3 py-2 text-sm font-medium text-action-fg focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50"
        >
          Bỏ qua điều hướng
        </a>

        {/* Desktop sidebar: the chart's margin, one neutral step away from the page. */}
        <aside className="sticky top-0 hidden h-dvh flex-col overflow-hidden border-r border-border bg-chrome lg:flex">
          {collapsed ? (
            <div className="flex flex-col items-center gap-3 px-2 py-5">
              <BrandMark compact />
              <ExpandButton collapsed={collapsed} onToggle={toggleCollapsed} />
            </div>
          ) : (
            <div className="flex items-center justify-between gap-2 px-4 py-5">
              <BrandMark />
              <ExpandButton collapsed={collapsed} onToggle={toggleCollapsed} />
            </div>
          )}
          <nav aria-label="Điều hướng chính" className={cn('flex-1 overflow-y-auto', collapsed ? 'px-2' : 'px-3')}>
            <Navigation collapsed={collapsed} />
          </nav>
          <SidebarFooter compact={collapsed} />
        </aside>

        {/* Mobile top bar with a collapsible navigation panel */}
        <header className="sticky top-0 z-30 border-b border-border bg-chrome/95 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between px-4 py-2">
            <BrandMark />
            <IconButton
              label={menuOpen ? 'Đóng menu' : 'Mở menu'}
              icon={
                <span key={String(menuOpen)} className="animate-icon-in">
                  {menuOpen ? <IconClose /> : <IconMenu />}
                </span>
              }
              aria-expanded={menuOpen}
              aria-controls={MOBILE_NAV_ID}
              onClick={() => setOpenOnPath(menuOpen ? null : pathname)}
            />
          </div>
          {/*
            Always mounted so it can animate closed as well as open: the grid row
            grows from 0fr to 1fr. `inert` keeps the closed menu out of the tab order.
          */}
          <div
            id={MOBILE_NAV_ID}
            inert={!menuOpen}
            className={cn(
              'grid transition-[grid-template-rows,visibility] duration-250 ease-out',
              menuOpen ? 'visible grid-rows-[1fr]' : 'invisible grid-rows-[0fr]',
            )}
          >
            <div className="overflow-hidden">
              <div className="border-t border-border">
                <nav aria-label="Điều hướng chính" className="px-3 py-3">
                  <Navigation onNavigate={closeMenu} />
                </nav>
                <SidebarFooter />
              </div>
            </div>
          </div>
        </header>

        <main id="main" tabIndex={-1} className="min-w-0 outline-none">
          {/* Keyed by route: each page eases in, so the change of place is visible. */}
          <div key={pathname} className="animate-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </SystemStatusProvider>
  )
}

/** Folds the desktop sidebar to icons, or opens it again. Its name says what it will do. */
function ExpandButton({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <IconButton
      label={collapsed ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'}
      icon={<IconSidebar size={18} />}
      aria-expanded={!collapsed}
      onClick={onToggle}
    />
  )
}
