import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import { searchPlaces } from '../api'
import type { GeoPlace } from '../types'
import { PlaceSearch } from './PlaceSearch'

vi.mock('../api')

const daLat: GeoPlace = {
  name: 'Đà Lạt',
  display_name: 'Đà Lạt, Lâm Đồng, Việt Nam',
  lat: 11.94,
  lon: 108.45,
  category: null,
  type: null,
  osm_type: 'relation',
  osm_id: 1,
}

describe('PlaceSearch', () => {
  beforeEach(() => {
    vi.mocked(searchPlaces).mockReset()
  })

  it('searches after typing and returns the chosen place', async () => {
    vi.mocked(searchPlaces).mockResolvedValue([daLat])
    const onSelect = vi.fn()
    const user = userEvent.setup()
    render(<PlaceSearch label="Điểm đến" onSelect={onSelect} />)

    await user.type(screen.getByRole('combobox', { name: 'Điểm đến' }), 'Đà Lạt')
    await user.click(await screen.findByRole('option', { name: /Đà Lạt, Lâm Đồng/ }))

    expect(onSelect).toHaveBeenCalledWith({ name: 'Đà Lạt', lat: 11.94, lon: 108.45 })
    expect(screen.getByRole('combobox')).toHaveValue('Đà Lạt')
    expect(searchPlaces).toHaveBeenCalledTimes(1)
    expect(vi.mocked(searchPlaces).mock.calls[0]?.[0]).toBe('Đà Lạt')
  })

  it('can be used with the keyboard', async () => {
    vi.mocked(searchPlaces).mockResolvedValue([daLat])
    const onSelect = vi.fn()
    const user = userEvent.setup()
    render(<PlaceSearch label="Điểm đến" onSelect={onSelect} />)

    await user.type(screen.getByRole('combobox'), 'Đà')
    await screen.findByRole('option')
    await user.keyboard('{ArrowDown}{Enter}')

    expect(onSelect).toHaveBeenCalledWith({ name: 'Đà Lạt', lat: 11.94, lon: 108.45 })
  })

  it('does not search for a single character', async () => {
    const user = userEvent.setup()
    render(<PlaceSearch label="Điểm đến" onSelect={vi.fn()} />)

    await user.type(screen.getByRole('combobox'), 'Đ')
    await new Promise((resolve) => setTimeout(resolve, 600))

    expect(searchPlaces).not.toHaveBeenCalled()
  })

  it('says when nothing matches and when the search fails', async () => {
    vi.mocked(searchPlaces).mockResolvedValueOnce([])
    const user = userEvent.setup()
    render(<PlaceSearch label="Điểm đến" onSelect={vi.fn()} />)

    await user.type(screen.getByRole('combobox'), 'zzzz')
    expect(await screen.findByText(/Không tìm thấy địa điểm nào/)).toBeInTheDocument()

    vi.mocked(searchPlaces).mockRejectedValueOnce(
      new ApiError({ kind: 'server', message: 'Không kết nối được tới dịch vụ dữ liệu bên ngoài.' }),
    )
    await user.type(screen.getByRole('combobox'), 'y')
    expect(await screen.findByText('Không kết nối được tới dịch vụ dữ liệu bên ngoài.')).toBeInTheDocument()
  })
})
