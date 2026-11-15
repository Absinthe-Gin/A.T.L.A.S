import { IconCloud, IconRefresh } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { IconButton } from '@/components/ui/IconButton'
import { InlineAlert } from '@/components/ui/InlineAlert'

import { formatWeekday } from '../format'
import { useWeather } from '../hooks/useWeather'
import type { Place } from '../types'

const TIME = new Intl.DateTimeFormat('vi-VN', { hour: '2-digit', minute: '2-digit' })

function round(value: number): string {
  return `${Math.round(value)}°`
}

/** Current weather and a 7-day forecast for one place, kept up to date while shown. */
export function WeatherCard({ place }: { place: Place }) {
  const { data, updatedAt } = useWeather(place.lat, place.lon)
  const headingId = `weather-${place.lat}-${place.lon}`

  return (
    <Card aria-labelledby={headingId} className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 id={headingId} className="text-lg font-extrabold text-fg">
            Thời tiết
          </h2>
          <p className="truncate text-sm text-fg-muted">{place.name}</p>
        </div>
        <IconButton
          label="Cập nhật thời tiết"
          icon={<IconRefresh size={18} />}
          disabled={data.status === 'loading'}
          onClick={data.refresh}
        />
      </div>

      {data.status === 'loading' && (
        <div role="status" aria-label="Đang tải thời tiết" className="mt-4 space-y-3">
          <div className="h-16 animate-pulse rounded-control bg-surface-2" />
          <div className="h-20 animate-pulse rounded-control bg-surface-2" />
        </div>
      )}

      {data.status === 'error' && (
        <InlineAlert
          className="mt-4"
          title="Chưa lấy được thời tiết"
          requestId={data.error.requestId}
          action={
            <Button variant="secondary" size="sm" onClick={data.reload}>
              Thử lại
            </Button>
          }
        >
          {data.error.message}
        </InlineAlert>
      )}

      {data.status === 'success' && (
        <div className="mt-4 animate-settle space-y-4">
          <div className="flex items-center gap-4">
            <span className="flex size-14 shrink-0 items-center justify-center rounded-card bg-note-blue text-note-blue-ink">
              <IconCloud size={28} />
            </span>
            <div>
              <p className="text-4xl leading-none font-extrabold text-fg">{round(data.data.current.temperature_c)}</p>
              <p className="mt-1 text-sm font-semibold text-fg">{data.data.current.description}</p>
            </div>
          </div>

          <dl className="grid grid-cols-3 gap-2 text-center">
            {[
              ['Cảm giác', round(data.data.current.apparent_temperature_c)],
              ['Độ ẩm', `${data.data.current.humidity_percent}%`],
              ['Gió', `${Math.round(data.data.current.wind_speed_kmh)} km/h`],
            ].map(([term, value]) => (
              <div key={term} className="rounded-control bg-surface-2 px-2 py-2">
                <dt className="text-xs text-fg-subtle">{term}</dt>
                <dd className="text-sm font-bold text-fg">{value}</dd>
              </div>
            ))}
          </dl>

          <ol aria-label="Dự báo 7 ngày" className="divide-y divide-border">
            {data.data.daily.map((day) => (
              <li key={day.date} className="flex items-center gap-3 py-2 text-sm">
                <span className="w-20 shrink-0 font-semibold text-fg-muted">{formatWeekday(day.date)}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-fg">{day.description}</span>
                  {day.precipitation_probability_percent !== null && (
                    <span className="block text-xs text-accent">Mưa {day.precipitation_probability_percent}%</span>
                  )}
                </span>
                <span className="shrink-0 font-bold text-fg">
                  {round(day.temperature_max_c)}
                  <span className="font-medium text-fg-subtle"> {round(day.temperature_min_c)}</span>
                </span>
              </li>
            ))}
          </ol>

          <p className="text-xs text-fg-subtle">
            {updatedAt ? `Cập nhật lúc ${TIME.format(updatedAt)}, tự làm mới mỗi 10 phút. ` : ''}
            Nguồn: Open-Meteo.com
          </p>
        </div>
      )}
    </Card>
  )
}
