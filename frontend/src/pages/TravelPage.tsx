import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router'

import { PageContainer, PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { InlineAlert } from '@/components/ui/InlineAlert'
import { StickyNote } from '@/components/ui/StickyNote'
import { PlaceSearch } from '@/features/places'
import { PlanForm } from '@/features/travel/components/PlanForm'
import { PlanList } from '@/features/travel/components/PlanList'
import { type MapMarker, PinMap } from '@/components/map/PinMap'
import { WeatherCard } from '@/features/travel/components/WeatherCard'
import { useTravelPlans } from '@/features/travel/hooks/useTravelPlans'
import type { Place } from '@/features/travel/types'

function PlansSection() {
  const navigate = useNavigate()
  const plans = useTravelPlans()
  const { data } = plans

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-8 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <section aria-labelledby="plans-heading" className="space-y-4">
        <h2 id="plans-heading" className="text-lg font-extrabold text-fg">
          Chuyến đi của bạn
        </h2>
        {data.status === 'loading' && (
          <div role="status" aria-label="Đang tải chuyến đi" className="grid gap-3 sm:grid-cols-2">
            <div className="h-32 animate-pulse rounded-card bg-surface-2" />
            <div className="h-32 animate-pulse rounded-card bg-surface-2" />
          </div>
        )}
        {data.status === 'error' && (
          <InlineAlert
            title="Không tải được danh sách chuyến đi"
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
        {data.status === 'success' && <PlanList plans={data.data.items} total={data.data.total} />}
      </section>

      <div className="order-first lg:order-none">
        <StickyNote color="yellow" tape="center" className="p-5">
          <PlanForm
            onSubmit={plans.create}
            saving={plans.saving}
            onCreated={(plan) => navigate(`/travel/${plan.id}`)}
          />
        </StickyNote>
      </div>
    </div>
  )
}

function ExploreSection() {
  const [place, setPlace] = useState<Place | null>(null)
  const markers = useMemo<MapMarker[]>(
    () => (place ? [{ id: 'selected', place, kind: 'selected' }] : []),
    [place],
  )

  return (
    <section aria-labelledby="explore-heading" className="space-y-4">
      <div>
        <h2 id="explore-heading" className="text-lg font-extrabold text-fg">
          Khám phá địa điểm
        </h2>
        <p className="text-sm text-fg-muted">Tìm một nơi để xem trên bản đồ và xem thời tiết ở đó.</p>
      </div>
      <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <Card className="space-y-4 p-4">
          <PlaceSearch label="Tìm địa điểm" onSelect={setPlace} value={place} />
          <PinMap
            markers={markers}
            label={place ? `Bản đồ quanh ${place.name}` : 'Bản đồ Việt Nam'}
            className="h-80 sm:h-96"
          />
        </Card>
        {place ? (
          <WeatherCard key={`${place.lat},${place.lon}`} place={place} />
        ) : (
          <Card className="p-5">
            <h2 className="text-lg font-extrabold text-fg">Thời tiết</h2>
            <p className="mt-1 text-sm text-fg-muted">Chọn một địa điểm để xem thời tiết hiện tại và dự báo 7 ngày.</p>
          </Card>
        )}
      </div>
    </section>
  )
}

export function TravelPage() {
  return (
    <PageContainer>
      <PageHeader
        title="Du lịch"
        description="Lập kế hoạch chuyến đi, xem địa điểm trên bản đồ, thời tiết và cách đi tới nơi."
      />
      <PlansSection />
      <ExploreSection />
    </PageContainer>
  )
}
