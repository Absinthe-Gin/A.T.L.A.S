import { type FormEvent, type ReactNode, useId, useState } from 'react'

import { IconBus, IconExternal, IconPlane, IconTrain } from '@/components/icons'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonClasses'
import { Card } from '@/components/ui/Card'
import { errorClasses, fieldClasses, labelClasses } from '@/components/ui/fieldClasses'
import { InlineAlert } from '@/components/ui/InlineAlert'
import { formatVnd, toIsoDate } from '@/utils/money'

import { formatDate, formatDistance, formatDuration } from '../format'
import { useTransport } from '../hooks/useTransport'
import type { FlightOffer, FlightOptions, Place, RoadOption, TransportLink, TransportOptions } from '../types'
import { PlaceSearch } from '@/features/places'

interface TransportPanelProps {
  destination: Place
  /** Suggested travel date, e.g. the plan's first day. */
  defaultDate?: string | null
}

/** Search ways to get to `destination`: road, flights with prices when available, train and coach sites. */
export function TransportPanel({ destination, defaultDate }: TransportPanelProps) {
  const id = useId()
  const [origin, setOrigin] = useState<Place | null>(null)
  const [travelDate, setTravelDate] = useState(() => defaultDate ?? toIsoDate(new Date()))
  const [adults, setAdults] = useState(1)
  const [touched, setTouched] = useState(false)
  const { state, search } = useTransport()

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    if (!origin || !travelDate) return
    search({ origin, destination, travel_date: travelDate, adults })
  }

  return (
    <Card aria-labelledby={`${id}-title`} className="p-5">
      <h2 id={`${id}-title`} className="text-lg font-extrabold text-fg">
        Cách đi tới {destination.name}
      </h2>
      <p className="mt-1 text-sm text-fg-muted">Máy bay, tàu hỏa và xe khách từ nơi bạn xuất phát.</p>

      <form onSubmit={handleSubmit} noValidate className="mt-4 grid gap-4 sm:grid-cols-[minmax(0,1fr)_10rem_6rem_auto] sm:items-start">
        <div>
          <PlaceSearch label="Đi từ" onSelect={setOrigin} value={origin} placeholder="Ví dụ: Hà Nội" />
          {touched && !origin && <p className={errorClasses}>Chọn nơi xuất phát trong danh sách gợi ý.</p>}
        </div>
        <div>
          <label htmlFor={`${id}-date`} className={labelClasses}>
            Ngày đi
          </label>
          <input
            id={`${id}-date`}
            type="date"
            required
            value={travelDate}
            onChange={(event) => setTravelDate(event.target.value)}
            className={fieldClasses(touched && !travelDate)}
          />
        </div>
        <div>
          <label htmlFor={`${id}-adults`} className={labelClasses}>
            Số khách
          </label>
          <select
            id={`${id}-adults`}
            value={adults}
            onChange={(event) => setAdults(Number(event.target.value))}
            className={fieldClasses()}
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((count) => (
              <option key={count} value={count}>
                {count}
              </option>
            ))}
          </select>
        </div>
        <Button type="submit" loading={state.status === 'loading'} className="sm:mt-7">
          Tìm cách đi
        </Button>
      </form>

      <div aria-live="polite" className="mt-5">
        {state.status === 'error' && (
          <InlineAlert title="Chưa tìm được cách đi" requestId={state.error.requestId}>
            {state.error.message}
          </InlineAlert>
        )}
        {state.status === 'success' && <TransportResults options={state.data} />}
      </div>
    </Card>
  )
}

function TransportResults({ options }: { options: TransportOptions }) {
  return (
    <div className="animate-settle space-y-4">
      <p className="text-sm text-fg-muted">
        {options.origin.name} đến {options.destination.name}, ngày {formatDate(options.travel_date)}. Khoảng cách đường
        chim bay {formatDistance(options.straight_distance_km)}.
      </p>
      <div className="grid gap-4 lg:grid-cols-2">
        <FlightSection flights={options.flights} />
        <div className="space-y-4">
          <RoadSection road={options.road} />
          {options.ground_links.map((link) => (
            <GroundLink key={link.mode} link={link} />
          ))}
        </div>
      </div>
    </div>
  )
}

function Section({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <section className="rounded-control border border-border bg-surface-2/50 p-4">
      <h3 className="flex items-center gap-2 text-[0.9375rem] font-bold text-fg">
        <span className="text-primary">{icon}</span>
        {title}
      </h3>
      <div className="mt-2 space-y-2 text-sm text-fg-muted">{children}</div>
    </section>
  )
}

function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={buttonClasses('secondary', 'sm')}>
      {children}
      <IconExternal size={14} />
      <span className="sr-only">(mở trang mới)</span>
    </a>
  )
}

const FLIGHT_STATUS_LABEL: Record<FlightOptions['status'], string> = {
  ok: 'Có giá vé',
  not_configured: 'Chưa có giá vé',
  no_airport: 'Không có sân bay gần',
  too_close: 'Quá gần',
  unavailable: 'Tạm thời lỗi',
}

function FlightSection({ flights }: { flights: FlightOptions }) {
  const route =
    flights.origin_airport && flights.destination_airport
      ? `${flights.origin_airport} đến ${flights.destination_airport}`
      : null
  return (
    <Section icon={<IconPlane size={18} />} title="Máy bay">
      <p className="flex flex-wrap items-center gap-2">
        <Badge tone={flights.status === 'ok' ? 'success' : 'neutral'}>{FLIGHT_STATUS_LABEL[flights.status]}</Badge>
        {route && <span className="font-mono text-xs">{route}</span>}
      </p>
      {flights.message && <p>{flights.message}</p>}
      {flights.offers.length > 0 && (
        <ul className="divide-y divide-border rounded-control border border-border bg-surface">
          {flights.offers.map((offer, index) => (
            <FlightRow key={`${offer.segments.map((s) => s.flight_number ?? s.departure_time).join('-')}-${index}`} offer={offer} />
          ))}
        </ul>
      )}
      {flights.source && <p className="text-xs text-fg-subtle">Nguồn: {flights.source}. Giá có thể thay đổi khi đặt.</p>}
      {flights.search_url && <ExternalLink href={flights.search_url}>Mở Google Flights</ExternalLink>}
    </Section>
  )
}

function FlightRow({ offer }: { offer: FlightOffer }) {
  const first = offer.segments[0]
  const last = offer.segments[offer.segments.length - 1]
  const airlines = [...new Set(offer.segments.map((segment) => segment.airline))].join(', ')
  return (
    <li className="flex items-center gap-3 px-3 py-2.5">
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-fg">{airlines}</p>
        <p className="truncate text-xs text-fg-subtle">
          {first.departure_time.slice(-5)} đến {last.arrival_time.slice(-5)}
          {offer.total_duration_minutes !== null && `, ${formatDuration(offer.total_duration_minutes)}`}
          {offer.stops === 0 ? ', bay thẳng' : `, ${offer.stops} điểm dừng`}
        </p>
      </div>
      <p className="shrink-0 font-bold text-fg">{offer.price_vnd !== null ? formatVnd(offer.price_vnd) : 'Chưa có giá'}</p>
    </li>
  )
}

function RoadSection({ road }: { road: RoadOption }) {
  return (
    <Section icon={<IconBus size={18} />} title="Đường bộ">
      {road.status === 'ok' && road.distance_km !== null && road.duration_minutes !== null ? (
        <p>
          <span className="font-bold text-fg">{formatDistance(road.distance_km)}</span>, lái xe khoảng{' '}
          <span className="font-bold text-fg">{formatDuration(road.duration_minutes)}</span> không tính nghỉ. Xe khách
          thường lâu hơn.
        </p>
      ) : (
        <p>{road.message}</p>
      )}
      <p className="text-xs text-fg-subtle">Ước tính bởi OSRM trên dữ liệu OpenStreetMap.</p>
    </Section>
  )
}

function GroundLink({ link }: { link: TransportLink }) {
  return (
    <Section
      icon={link.mode === 'train' ? <IconTrain size={18} /> : <IconBus size={18} />}
      title={link.mode === 'train' ? 'Tàu hỏa' : 'Xe khách'}
    >
      <p>{link.hint}</p>
      <p className="text-xs text-fg-subtle">Atlas chưa có giờ chạy và giá vé của {link.provider}.</p>
      <ExternalLink href={link.url}>Mở {link.provider}</ExternalLink>
    </Section>
  )
}
