import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import { addItem, deletePlan, getPlan, getWeather } from '../api'
import type { PlanDetail } from '../types'
import { PlanView } from './PlanView'

vi.mock('../api')
// Leaflet draws into the DOM itself; the map is not what these tests check.
vi.mock('@/components/map/PinMap', () => ({
  PinMap: ({ label, markers }: { label: string; markers: { id: string }[] }) => (
    <div role="region" aria-label={label} data-markers={markers.map((m) => m.id).join(',')} />
  ),
}))

const plan: PlanDetail = {
  id: 'p1',
  title: 'Đà Lạt cuối năm',
  destination: { name: 'Đà Lạt', lat: 11.94, lon: 108.45 },
  start_date: '2026-12-01',
  end_date: '2026-12-02',
  note: null,
  item_count: 2,
  created_at: '2026-11-15T00:00:00Z',
  items: [
    {
      id: 'i1',
      title: 'Hồ Xuân Hương',
      day: '2026-12-01',
      start_time: '07:30:00',
      place: { name: 'Hồ Xuân Hương', lat: 11.94, lon: 108.44 },
      note: null,
    },
    { id: 'i2', title: 'Cà phê', day: '2026-12-02', start_time: null, place: null, note: 'Tùng' },
  ],
}

function renderPlan() {
  const router = createMemoryRouter(
    [
      { path: '/travel/:planId', element: <PlanView planId="p1" /> },
      { path: '/travel', element: <h1>Danh sách</h1> },
    ],
    { initialEntries: ['/travel/p1'] },
  )
  render(<RouterProvider router={router} />)
  return router
}

describe('PlanView', () => {
  beforeEach(() => {
    vi.mocked(getPlan).mockReset().mockResolvedValue(plan)
    vi.mocked(getWeather).mockReturnValue(new Promise(() => {}))
  })

  it('shows the plan, its stops on the map and its itinerary by day', async () => {
    renderPlan()

    expect(await screen.findByRole('heading', { level: 1, name: 'Đà Lạt cuối năm' })).toBeInTheDocument()
    expect(screen.getByText('01/12/2026 – 02/12/2026')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: /Bản đồ chuyến đi/ })).toHaveAttribute('data-markers', 'destination,i1')
    const itinerary = screen.getByRole('heading', { name: 'Lịch trình' }).closest('section')!
    expect(within(itinerary).getByText('07:30')).toBeInTheDocument()
    expect(within(itinerary).getByText('Tùng')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Cách đi tới Đà Lạt' })).toBeInTheDocument()
  })

  it('adds an activity and reloads the plan', async () => {
    vi.mocked(addItem).mockResolvedValue(plan.items[0]!)
    const user = userEvent.setup()
    renderPlan()

    await user.type(await screen.findByRole('textbox', { name: 'Hoạt động' }), 'Chợ đêm')
    await user.click(screen.getByRole('button', { name: 'Thêm vào lịch trình' }))

    expect(addItem).toHaveBeenCalledWith('p1', {
      title: 'Chợ đêm',
      day: '2026-12-01',
      start_time: null,
      place: null,
      note: null,
    })
    await vi.waitFor(() => expect(getPlan).toHaveBeenCalledTimes(2))
  })

  it('deletes the plan after confirmation and returns to the list', async () => {
    vi.mocked(deletePlan).mockResolvedValue()
    const user = userEvent.setup()
    const router = renderPlan()

    await user.click(await screen.findByRole('button', { name: 'Xóa chuyến đi' }))
    expect(deletePlan).not.toHaveBeenCalled()
    await user.click(screen.getAllByRole('button', { name: 'Xóa chuyến đi' })[0]!)

    expect(deletePlan).toHaveBeenCalledWith('p1')
    await vi.waitFor(() => expect(router.state.location.pathname).toBe('/travel'))
  })

  it('says when the plan does not exist', async () => {
    vi.mocked(getPlan).mockRejectedValue(
      new ApiError({ kind: 'not_found', status: 404, message: 'Không tìm thấy kế hoạch du lịch.' }),
    )
    renderPlan()

    expect(await screen.findByText('Không tìm thấy chuyến đi')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Thử lại' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tất cả chuyến đi' })).toHaveAttribute('href', '/travel')
  })
})
