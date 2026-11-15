import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import { getWeather } from '../api'
import { WEATHER_REFRESH_MS } from '../hooks/useWeather'
import type { WeatherForecast } from '../types'
import { WeatherCard } from './WeatherCard'

vi.mock('../api')

const place = { name: 'Đà Lạt', lat: 11.94, lon: 108.45 }

function forecast(temperature: number): WeatherForecast {
  return {
    latitude: 11.94,
    longitude: 108.45,
    timezone: 'Asia/Ho_Chi_Minh',
    current: {
      observed_at: '2026-12-01T09:00',
      temperature_c: temperature,
      apparent_temperature_c: 16.2,
      humidity_percent: 81,
      wind_speed_kmh: 6.5,
      precipitation_mm: 0,
      weather_code: 3,
      description: 'Nhiều mây',
    },
    daily: [
      {
        date: '2026-12-01',
        temperature_max_c: 22,
        temperature_min_c: 14,
        precipitation_probability_percent: 70,
        weather_code: 61,
        description: 'Mưa nhỏ',
      },
    ],
    source: 'Weather data by Open-Meteo.com',
  }
}

describe('WeatherCard', () => {
  beforeEach(() => {
    vi.mocked(getWeather).mockReset()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows current conditions, the forecast and the source', async () => {
    vi.mocked(getWeather).mockResolvedValue(forecast(18.4))
    render(<WeatherCard place={place} />)

    expect(screen.getByRole('status', { name: 'Đang tải thời tiết' })).toBeInTheDocument()
    expect(await screen.findByText('18°')).toBeInTheDocument()
    expect(screen.getByText('Nhiều mây')).toBeInTheDocument()
    expect(screen.getByText('81%')).toBeInTheDocument()
    expect(screen.getByText('Mưa 70%')).toBeInTheDocument()
    expect(screen.getByText(/Nguồn: Open-Meteo.com/)).toBeInTheDocument()
    expect(getWeather).toHaveBeenCalledWith(11.94, 108.45, expect.any(AbortSignal))
  })

  it('refreshes by itself every ten minutes', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    vi.mocked(getWeather).mockResolvedValueOnce(forecast(18)).mockResolvedValueOnce(forecast(21))
    render(<WeatherCard place={place} />)
    expect(await screen.findByText('18°')).toBeInTheDocument()

    await act(async () => {
      await vi.advanceTimersByTimeAsync(WEATHER_REFRESH_MS)
    })

    expect(await screen.findByText('21°')).toBeInTheDocument()
    expect(getWeather).toHaveBeenCalledTimes(2)
  })

  it('shows the error with a retry', async () => {
    vi.mocked(getWeather)
      .mockRejectedValueOnce(new ApiError({ kind: 'timeout', message: 'Dịch vụ phản hồi quá lâu.', requestId: 'r1' }))
      .mockResolvedValueOnce(forecast(19))
    const user = userEvent.setup()
    render(<WeatherCard place={place} />)

    expect(await screen.findByText('Dịch vụ phản hồi quá lâu.')).toBeInTheDocument()
    expect(screen.getByText('r1')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Thử lại' }))
    expect(await screen.findByText('19°')).toBeInTheDocument()
  })
})
