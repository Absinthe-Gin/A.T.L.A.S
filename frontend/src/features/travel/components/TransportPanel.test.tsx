import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getTransport } from '../api'
import { searchPlaces } from '@/features/places'
import type { FlightOptions, TransportOptions } from '../types'
import { TransportPanel } from './TransportPanel'

vi.mock('../api')
vi.mock('@/features/places/api')

const destination = { name: 'Đà Lạt', lat: 11.94, lon: 108.45 }
const hanoi = { name: 'Hà Nội', lat: 21.03, lon: 105.85 }

function options(flights: Partial<FlightOptions> = {}): TransportOptions {
  return {
    origin: hanoi,
    destination,
    travel_date: '2026-12-01',
    straight_distance_km: 1020.4,
    road: { status: 'ok', distance_km: 1480.2, duration_minutes: 1500, message: null },
    flights: {
      status: 'ok',
      origin_airport: 'HAN',
      destination_airport: 'DLI',
      offers: [
        {
          price_vnd: 1_250_000,
          total_duration_minutes: 115,
          stops: 0,
          segments: [
            {
              airline: 'Vietjet',
              flight_number: 'VJ 401',
              departure_airport: 'HAN',
              departure_time: '2026-12-01 06:00',
              arrival_airport: 'DLI',
              arrival_time: '2026-12-01 07:55',
              duration_minutes: 115,
            },
          ],
        },
      ],
      search_url: 'https://www.google.com/travel/flights?q=x',
      message: null,
      source: 'Google Flights qua SerpApi',
      ...flights,
    },
    ground_links: [
      { mode: 'train', provider: 'Đường sắt Việt Nam (dsvn.vn)', url: 'https://dsvn.vn/', hint: 'Chọn ga đi và ga đến.' },
      { mode: 'bus', provider: 'Vexere', url: 'https://vexere.com/', hint: 'Tìm xe khách.' },
    ],
  }
}

async function searchFromHanoi() {
  const user = userEvent.setup()
  render(<TransportPanel destination={destination} defaultDate="2026-12-01" />)
  await user.type(screen.getByRole('combobox', { name: 'Đi từ' }), 'Hà Nội')
  await user.click(await screen.findByRole('option', { name: /Hà Nội/ }))
  await user.click(screen.getByRole('button', { name: 'Tìm cách đi' }))
  return user
}

describe('TransportPanel', () => {
  beforeEach(() => {
    vi.mocked(getTransport).mockReset()
    vi.mocked(searchPlaces).mockResolvedValue([
      { ...hanoi, display_name: 'Hà Nội, Việt Nam', category: null, type: null, osm_type: null, osm_id: 2 },
    ])
  })

  it('asks for an origin before searching', async () => {
    const user = userEvent.setup()
    render(<TransportPanel destination={destination} />)

    await user.click(screen.getByRole('button', { name: 'Tìm cách đi' }))

    expect(screen.getByText('Chọn nơi xuất phát trong danh sách gợi ý.')).toBeInTheDocument()
    expect(getTransport).not.toHaveBeenCalled()
  })

  it('shows flight prices, the road estimate and booking sites', async () => {
    vi.mocked(getTransport).mockResolvedValue(options())
    await searchFromHanoi()

    expect(getTransport).toHaveBeenCalledWith(
      { origin: hanoi, destination, travel_date: '2026-12-01', adults: 1 },
      expect.any(AbortSignal),
    )
    expect(await screen.findByText('Có giá vé')).toBeInTheDocument()
    expect(screen.getByText('Vietjet')).toBeInTheDocument()
    expect(screen.getByText(/1\.250\.000/)).toBeInTheDocument()
    expect(screen.getByText('1.480 km')).toBeInTheDocument()
    expect(screen.getByText('25 giờ')).toBeInTheDocument()
    const train = screen.getByRole('link', { name: /Mở Đường sắt Việt Nam/ })
    expect(train).toHaveAttribute('href', 'https://dsvn.vn/')
    expect(train).toHaveAttribute('target', '_blank')
    expect(screen.getByRole('link', { name: /Mở Vexere/ })).toHaveAttribute('href', 'https://vexere.com/')
  })

  it('offers a Google Flights link when prices are not configured', async () => {
    vi.mocked(getTransport).mockResolvedValue(
      options({
        status: 'not_configured',
        offers: [],
        source: null,
        message: 'Chưa cấu hình SERPAPI_API_KEY nên Atlas chưa lấy được giá vé. Mở Google Flights để xem.',
      }),
    )
    await searchFromHanoi()

    const flights = (await screen.findByRole('heading', { name: 'Máy bay' })).closest('section')!
    expect(within(flights).getByText('Chưa có giá vé')).toBeInTheDocument()
    expect(within(flights).getByText(/SERPAPI_API_KEY/)).toBeInTheDocument()
    expect(within(flights).getByRole('link', { name: /Mở Google Flights/ })).toHaveAttribute(
      'href',
      'https://www.google.com/travel/flights?q=x',
    )
  })
})
