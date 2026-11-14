import { render, screen } from '@testing-library/react'
import { createMemoryRouter, type RouteObject, RouterProvider } from 'react-router'
import { describe, expect, it, vi } from 'vitest'

import { getHealth } from '@/features/system-status/api'
import { RouteErrorPage } from '@/pages/RouteErrorPage'

import { AppLayout } from './layouts/AppLayout'
import { routes } from './router'

vi.mock('@/features/system-status/api')

function renderAt(path: string, routeConfig: RouteObject[] = routes) {
  const router = createMemoryRouter(routeConfig, { initialEntries: [path] })
  return render(<RouterProvider router={router} />)
}

describe('application routes', () => {
  it('renders the home page inside the layout at "/"', async () => {
    vi.mocked(getHealth).mockReturnValue(new Promise(() => {}))

    renderAt('/')

    expect(await screen.findByRole('heading', { level: 1, name: 'Xin chào' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Điều hướng chính' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Trạng thái hệ thống' })).toBeInTheDocument()
  })

  it('renders the not-found page for an unknown path', async () => {
    renderAt('/khong-ton-tai')

    expect(
      await screen.findByRole('heading', { name: 'Không tìm thấy trang' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Về trang chủ' })).toHaveAttribute('href', '/')
  })

  it('keeps the layout usable when a page fails to render', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    function BrokenPage(): never {
      throw new Error('render failure')
    }
    const routesWithBrokenPage: RouteObject[] = [
      {
        element: <AppLayout />,
        children: [
          {
            errorElement: <RouteErrorPage />,
            children: [{ index: true, element: <BrokenPage /> }],
          },
        ],
      },
    ]

    renderAt('/', routesWithBrokenPage)

    expect(await screen.findByRole('alert')).toHaveTextContent('Trang này gặp lỗi')
    expect(screen.getByRole('navigation', { name: 'Điều hướng chính' })).toBeInTheDocument()
  })
})
