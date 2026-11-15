import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import { IconArrowLeft, IconCalendar, IconMapPin } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { buttonClasses } from '@/components/ui/buttonClasses'
import { Card } from '@/components/ui/Card'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'

import { formatDateRange } from '../format'
import { usePlan } from '../hooks/useTravelPlans'
import { stopNumbers } from '../itinerary'
import type { PlanDetail } from '../types'
import { Itinerary } from './Itinerary'
import { PlaceSearch } from '@/features/places'
import { type MapMarker, PinMap } from '@/components/map/PinMap'
import { TransportPanel } from './TransportPanel'
import { WeatherCard } from './WeatherCard'

function planMarkers(plan: PlanDetail): MapMarker[] {
  const markers: MapMarker[] = []
  if (plan.destination) markers.push({ id: 'destination', place: plan.destination, kind: 'destination' })
  const numbers = stopNumbers(plan.items)
  for (const item of plan.items) {
    if (item.place) {
      markers.push({ id: item.id, place: item.place, kind: 'stop', badge: String(numbers.get(item.id)) })
    }
  }
  return markers
}

const backLink = (
  <Link to="/travel" className={buttonClasses('ghost', 'sm')}>
    <IconArrowLeft size={16} />
    Tất cả chuyến đi
  </Link>
)

/** One travel plan: map, weather, itinerary and ways to get there. */
export function PlanView({ planId }: { planId: string }) {
  const navigate = useNavigate()
  const plan = usePlan(planId)
  const { data } = plan
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [actionError, setActionError] = useState<ApiError | null>(null)
  const markers = useMemo(() => (data.status === 'success' ? planMarkers(data.data) : []), [data])

  if (data.status === 'loading') {
    return (
      <div role="status" aria-label="Đang tải chuyến đi" className="space-y-6">
        <div className="h-16 animate-pulse rounded-card bg-surface-2" />
        <div className="h-96 animate-pulse rounded-card bg-surface-2" />
      </div>
    )
  }

  if (data.status === 'error') {
    return (
      <div className="space-y-4">
        {backLink}
        <InlineAlert
          title={data.error.status === 404 ? 'Không tìm thấy chuyến đi' : 'Không tải được chuyến đi'}
          requestId={data.error.requestId}
          action={
            data.error.status === 404 ? undefined : (
              <Button variant="secondary" size="sm" onClick={data.reload}>
                Thử lại
              </Button>
            )
          }
        >
          {data.error.message}
        </InlineAlert>
      </div>
    )
  }

  const detail = data.data
  const dates = formatDateRange(detail.start_date, detail.end_date)

  const handleDelete = async () => {
    const result = await plan.remove()
    if (result.ok) navigate('/travel')
    else setActionError(result.error)
  }

  const handleDestination = async (place: PlanDetail['destination']) => {
    const result = await plan.update({ destination: place })
    setActionError(result.ok ? null : result.error)
  }

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        {backLink}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <h1 className="text-4xl font-extrabold tracking-tight text-fg text-balance">{detail.title}</h1>
            <p className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-fg-muted">
              <span className="flex items-center gap-1.5">
                <IconMapPin size={17} className="text-note-yellow-ink" />
                {detail.destination?.name ?? 'Chưa chọn điểm đến'}
              </span>
              <span className="flex items-center gap-1.5">
                <IconCalendar size={17} className="text-note-yellow-ink" />
                {dates ?? 'Chưa chọn ngày'}
              </span>
            </p>
          </div>
          {confirmingDelete ? (
            <div className="flex shrink-0 items-center gap-2">
              <Button variant="danger" size="sm" loading={plan.saving} onClick={() => void handleDelete()}>
                Xóa chuyến đi
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setConfirmingDelete(false)}>
                Giữ lại
              </Button>
            </div>
          ) : (
            <Button variant="ghost" size="sm" className="self-start sm:self-auto" onClick={() => setConfirmingDelete(true)}>
              Xóa chuyến đi
            </Button>
          )}
        </div>
        {actionError && (
          <InlineAlert title="Chưa lưu được thay đổi" requestId={actionError.requestId}>
            {actionError.message}
          </InlineAlert>
        )}
      </header>

      <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-6">
          <PinMap
            markers={markers}
            label={`Bản đồ chuyến đi ${detail.title}`}
            className="h-80 sm:h-[26rem]"
          />
          <Itinerary
            plan={detail}
            saving={plan.saving}
            onAdd={plan.addItem}
            onDelete={(itemId) => void plan.removeItem(itemId)}
          />
        </div>
        <div className="space-y-6">
          {detail.destination ? (
            <WeatherCard key={`${detail.destination.lat},${detail.destination.lon}`} place={detail.destination} />
          ) : (
            <Card className="p-5">
              <h2 className="text-lg font-extrabold text-fg">Chọn điểm đến</h2>
              <p className="mt-1 mb-3 text-sm text-fg-muted">
                Có điểm đến thì Atlas mới xem được thời tiết và cách đi.
              </p>
              <PlaceSearch label="Điểm đến" onSelect={(place) => void handleDestination(place)} />
            </Card>
          )}
        </div>
      </div>

      {detail.destination && <TransportPanel destination={detail.destination} defaultDate={detail.start_date} />}
    </div>
  )
}
