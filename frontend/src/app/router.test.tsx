import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, type RouteObject, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getHealth } from '@/features/system-status/api'
import { RouteErrorPage } from '@/pages/RouteErrorPage'

import { AppLayout } from './layouts/AppLayout'
import { routes } from './router'

vi.mock('@/features/system-status/api')

function renderAt(path: string, routeConfig: RouteObject[] = routes) {
  const router = createMemoryRouter(routeConfig, { initialEntries: [path] })
  return { router, ...render(<RouterProvider router={router} />) }
}

const mainNav = () => screen.getAllByRole('navigation', { name: 'Điều hướng chính' })[0]!

describe('application routes', () => {
  beforeEach(() => {
    vi.mocked(getHealth).mockReturnValue(new Promise(() => {}))
  })

  it('renders the dashboard inside the layout at "/"', async () => {
    renderAt('/')

    expect(await screen.findByRole('heading', { level: 1, name: /^Chào buổi/ })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Trạng thái hệ thống' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Các phân hệ' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Trò chuyện với Atlas' })).toHaveAttribute('href', '/chat')
    expect(screen.getByRole('link', { name: 'Bỏ qua điều hướng' })).toHaveAttribute('href', '#main')
  })

  it('lists every module in the navigation and marks the current page', async () => {
    renderAt('/chat')

    const nav = mainNav()
    const labels = within(nav)
      .getAllByRole('link')
      .map((link) => link.textContent)
    expect(labels).toEqual(['Tổng quan', 'Trợ lý AI', 'Tài chínhSắp có', 'Du lịchSắp có', 'Ẩm thựcSắp có', 'Ghi nhớSắp có'])
    expect(within(nav).getByRole('link', { name: 'Trợ lý AI' })).toHaveAttribute('aria-current', 'page')
    expect(within(nav).getByRole('link', { name: 'Tổng quan' })).not.toHaveAttribute('aria-current')
  })

  it('renders the chat page at "/chat"', async () => {
    renderAt('/chat')

    expect(await screen.findByRole('heading', { level: 1, name: 'Trợ lý AI' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Tin nhắn' })).toBeInTheDocument()
  })

  it.each([
    ['/finance', 'Tài chính'],
    ['/travel', 'Du lịch'],
    ['/food', 'Ẩm thực'],
    ['/memory', 'Ghi nhớ'],
  ])('states plainly that %s is not implemented yet', async (path, title) => {
    renderAt(path)

    expect(await screen.findByRole('heading', { level: 1, name: title })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Phân hệ chưa được triển khai' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Chức năng dự kiến' })).toBeInTheDocument()
  })

  it('renders the not-found page for an unknown path', async () => {
    renderAt('/khong-ton-tai')

    expect(await screen.findByRole('heading', { name: 'Không tìm thấy trang' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Về trang chủ' })).toHaveAttribute('href', '/')
  })

  it('opens the mobile menu and closes it after navigating', async () => {
    const user = userEvent.setup()
    const { router } = renderAt('/')
    const toggle = screen.getByRole('button', { name: 'Mở menu' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    // Closed but still mounted so it can animate: kept out of the tab order.
    expect(document.getElementById('mobile-navigation')).toHaveAttribute('inert')

    await user.click(toggle)
    expect(screen.getByRole('button', { name: 'Đóng menu' })).toHaveAttribute('aria-expanded', 'true')
    expect(document.getElementById('mobile-navigation')).not.toHaveAttribute('inert')
    const mobileNav = screen.getAllByRole('navigation', { name: 'Điều hướng chính' })[1]!
    await user.click(within(mobileNav).getByRole('link', { name: 'Trợ lý AI' }))

    expect(router.state.location.pathname).toBe('/chat')
    expect(screen.getByRole('button', { name: 'Mở menu' })).toHaveAttribute('aria-expanded', 'false')
  })

  it('closes the mobile menu with Escape', async () => {
    const user = userEvent.setup()
    renderAt('/')
    await user.click(screen.getByRole('button', { name: 'Mở menu' }))

    await user.keyboard('{Escape}')

    expect(screen.getByRole('button', { name: 'Mở menu' })).toHaveAttribute('aria-expanded', 'false')
  })

  it('keeps the layout usable when a page fails to render', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    function BrokenPage(): never {
      throw new Error('render failure')
    }
    const routesWithBrokenPage: RouteObject[] = [
      {
        element: <AppLayout />,
        children: [{ errorElement: <RouteErrorPage />, children: [{ index: true, element: <BrokenPage /> }] }],
      },
    ]

    renderAt('/', routesWithBrokenPage)

    expect(await screen.findByRole('alert')).toHaveTextContent('Trang này gặp lỗi')
    expect(mainNav()).toBeInTheDocument()
  })
})
