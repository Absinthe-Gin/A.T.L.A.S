import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import type { DishSearchResult, Restaurant } from '../types'
import { restaurantMarkers } from '../markers'
import { RestaurantResults } from './RestaurantResults'

vi.mock('@/components/map/PinMap', () => ({
  PinMap: ({ markers }: { markers: { id: string; kind: string; badge?: string }[] }) => (
    <div role="region" aria-label="Bản đồ" data-markers={markers.map((m) => `${m.kind}:${m.badge ?? ''}`).join(',')} />
  ),
}))

const origin = { name: 'Hà Nội', lat: 21.03, lon: 105.85 }

function restaurant(name: string, distance: number, id: number): Restaurant {
  return {
    name,
    cuisine: 'vietnamese',
    address: 'Lò Đúc',
    opening_hours: '06:00-22:00',
    phone: null,
    website: null,
    lat: 21.03 + id / 1000,
    lon: 105.85,
    distance_km: distance,
    osm_type: 'node',
    osm_id: id,
  }
}

const found: DishSearchResult = {
  dish: 'phở',
  radius_m: 5000,
  status: 'ok',
  restaurants: [restaurant('Phở Thìn', 0.4, 1), restaurant('Phở Bát Đàn', 1.2, 2)],
  message: null,
  source: '© OpenStreetMap contributors (Overpass API)',
}

const noResults: DishSearchResult = {
  ...found,
  status: 'no_results',
  restaurants: [],
  message: 'Không có quán nào có tên chứa "phở" trong bán kính 5 km trên OpenStreetMap.',
}

const baseProps = {
  origin,
  loading: false,
  error: null,
  onRetry: () => {},
  selectedIndex: null,
  onSelect: () => {},
}

describe('RestaurantResults', () => {
  it('lists restaurants with distance, numbered on the map', () => {
    render(<RestaurantResults {...baseProps} result={found} />)

    expect(screen.getByText('Phở Thìn')).toBeInTheDocument()
    expect(screen.getByText('0,4 km')).toBeInTheDocument()
    expect(screen.getByText('1,2 km')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Bản đồ' })).toHaveAttribute('data-markers', 'selected:,stop:1,stop:2')
    expect(screen.getAllByText(/Giờ mở cửa: 06:00-22:00/)).toHaveLength(2)
    expect(screen.getByText(/Nguồn: © OpenStreetMap contributors/)).toBeInTheDocument()
  })

  it('states that the data has no match instead of showing an empty map', () => {
    render(<RestaurantResults {...baseProps} result={noResults} />)

    expect(screen.getByText('Chưa có quán nào trong dữ liệu')).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Bản đồ' })).not.toBeInTheDocument()
    expect(screen.getByText(/Không có quán nào/)).toBeInTheDocument()
  })

  it('reports a failed search with its request id and a retry', async () => {
    const onRetry = vi.fn()
    const user = userEvent.setup()
    render(
      <RestaurantResults
        {...baseProps}
        result={null}
        onRetry={onRetry}
        error={new ApiError({ kind: 'external', message: 'Dịch vụ bên ngoài đang gặp sự cố.', requestId: 'r9' })}
      />,
    )

    expect(screen.getByText('Dịch vụ bên ngoài đang gặp sự cố.')).toBeInTheDocument()
    expect(screen.getByText('r9')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Thử lại' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('reports the selected restaurant when the user picks one', async () => {
    const onSelect = vi.fn()
    const user = userEvent.setup()
    render(<RestaurantResults {...baseProps} result={found} onSelect={onSelect} />)

    await user.click(screen.getByRole('button', { name: /Phở Bát Đàn/ }))

    expect(onSelect).toHaveBeenCalledWith(1)
  })
})

describe('restaurantMarkers', () => {
  it('highlights the selected restaurant and keeps the origin first', () => {
    const markers = restaurantMarkers(origin, found.restaurants, 0)

    expect(markers.map((m) => m.kind)).toEqual(['selected', 'selected', 'stop'])
    expect(markers[0]?.id).toBe('origin')
  })

  it('draws no origin pin when the origin is unknown', () => {
    expect(restaurantMarkers(null, found.restaurants, null)).toHaveLength(2)
  })
})
