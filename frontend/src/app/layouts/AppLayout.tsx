import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router'

import { IconClose, IconMenu } from '@/components/icons'
import { IconButton } from '@/components/ui/IconButton'
import { SystemStatusIndicator } from '@/features/system-status/components/SystemStatusIndicator'
import { SystemStatusProvider } from '@/features/system-status/SystemStatusProvider'
import { cn } from '@/utils/cn'

import { BrandMark } from './BrandMark'
import { Navigation } from './Navigation'
import { ThemeToggle } from './ThemeToggle'

const MOBILE_NAV_ID = 'mobile-navigation'

function SidebarFooter() {
  return (
    <div className="flex items-center gap-2 border-t border-border px-4 py-3">
      <div className="min-w-0 flex-1">
        <SystemStatusIndicator />
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
      <div className="min-h-dvh bg-bg text-fg lg:grid lg:grid-cols-[15.5rem_1fr]">
        <a
          href="#main"
          className="sr-only rounded-control bg-action px-3 py-2 text-sm font-medium text-action-fg focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50"
        >
          Bỏ qua điều hướng
        </a>

        {/* Desktop sidebar: the chart's margin, one neutral step away from the page. */}
        <aside className="sticky top-0 hidden h-dvh flex-col border-r border-border bg-chrome lg:flex">
          <div className="px-4 py-5">
            <BrandMark />
          </div>
          <nav aria-label="Điều hướng chính" className="flex-1 overflow-y-auto px-3">
            <Navigation />
          </nav>
          <SidebarFooter />
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
