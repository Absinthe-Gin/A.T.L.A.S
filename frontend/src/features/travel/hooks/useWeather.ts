import { useCallback, useEffect, useState } from 'react'

import { type AsyncData, useAsyncData } from '@/hooks/useAsyncData'

import { getWeather } from '../api'
import type { WeatherForecast } from '../types'

/** Open-Meteo refreshes current conditions every 15 minutes; checking every 10 keeps the card current. */
export const WEATHER_REFRESH_MS = 10 * 60 * 1000

export interface UseWeather {
  data: AsyncData<WeatherForecast>
  /** When the shown forecast was received. */
  updatedAt: Date | null
}

/** Weather at one point, refreshed in the background while the card is on screen. */
export function useWeather(lat: number, lon: number): UseWeather {
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)
  const fetcher = useCallback(
    async (signal: AbortSignal) => {
      const forecast = await getWeather(lat, lon, signal)
      setUpdatedAt(new Date())
      return forecast
    },
    [lat, lon],
  )
  const data = useAsyncData(fetcher)
  const { refresh } = data

  useEffect(() => {
    const timer = window.setInterval(refresh, WEATHER_REFRESH_MS)
    return () => window.clearInterval(timer)
  }, [refresh])

  return { data, updatedAt }
}
