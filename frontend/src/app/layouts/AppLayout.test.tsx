import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getHealth } from '@/features/system-status/api'
import { SIDEBAR_STORAGE_KEY } from '@/hooks/useSidebarCollapsed'

import { AppLayout } from './AppLayout'

vi.mock('@/features/system-status/api')

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<p>Tổng quan</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('AppLayout sidebar', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.mocked(getHealth).mockReset().mockReturnValue(new Promise(() => {}))
  })

  it('folds and expands the desktop sidebar, and says what the button will do', async () => {
    const user = userEvent.setup()
    renderLayout()

    const fold = screen.getByRole('button', { name: 'Thu gọn thanh bên' })
    expect(fold).toHaveAttribute('aria-expanded', 'true')

    await user.click(fold)

    const expand = screen.getByRole('button', { name: 'Mở rộng thanh bên' })
    expect(expand).toHaveAttribute('aria-expanded', 'false')
    expect(window.localStorage.getItem(SIDEBAR_STORAGE_KEY)).toBe('1')
    // The mobile menu is mounted too (inert while closed): look only at the desktop sidebar.
    const desktop = screen.getAllByRole('navigation', { name: 'Điều hướng chính' })[0]!
    expect(within(desktop).getByRole('link', { name: 'Tài chính' })).toHaveClass('justify-center')

    await user.click(expand)

    expect(screen.getByRole('button', { name: 'Thu gọn thanh bên' })).toBeInTheDocument()
    expect(window.localStorage.getItem(SIDEBAR_STORAGE_KEY)).toBe('0')
  })

  it('opens already folded when the choice was saved before', () => {
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, '1')
    renderLayout()

    expect(screen.getByRole('button', { name: 'Mở rộng thanh bên' })).toBeInTheDocument()
  })
})
