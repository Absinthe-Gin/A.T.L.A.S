import { useState } from 'react'

import { PageContainer, PageHeader } from '@/components/PageHeader'
import { Card } from '@/components/ui/Card'
import { InlineAlert } from '@/components/ui/InlineAlert'
import { Button } from '@/components/ui/Button'
import { DishSearch } from '@/features/food/components/DishSearch'
import { OriginPicker } from '@/features/food/components/OriginPicker'
import { RegionDishes } from '@/features/food/components/RegionDishes'
import { RestaurantResults } from '@/features/food/components/RestaurantResults'
import { useRecommendation } from '@/features/food/hooks/useRecommendation'
import { useRestaurantSearch } from '@/features/food/hooks/useRestaurantSearch'
import type { RadiusM } from '@/features/food/types'
import type { Place } from '@/features/places'

/** Restaurants for one dish near the origin. Its own component so it resets when the origin changes. */
function RegionSection({ origin }: { origin: Place }) {
  const data = useRecommendation(origin)
  const restaurants = useRestaurantSearch()
  const [dish, setDish] = useState('')
  const [radiusM, setRadiusM] = useState<RadiusM>(5000)
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)

  const runSearch = (name: string) => {
    setDish(name)
    setSelectedIndex(null)
    restaurants.search({ dish: name, lat: origin.lat, lon: origin.lon, radiusM })
  }

  return (
    <>
      {data.status === 'loading' && (
        <div role="status" aria-label="Đang tải món đặc sản" className="h-48 animate-pulse rounded-card bg-surface-2" />
      )}
      {data.status === 'error' && (
        <InlineAlert
          title="Không tải được món đặc sản"
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
        <RegionDishes recommendation={data.data} onSearchDish={runSearch} disabled={restaurants.state.status === 'loading'} />
      )}

      <Card className="space-y-5 p-5">
        <DishSearch
          dish={dish}
            onDishChange={setDish}
          radiusM={radiusM}
          onRadiusChange={setRadiusM}
          onSubmit={() => runSearch(dish.trim())}
          searching={restaurants.state.status === 'loading'}
        />
      </Card>

      <RestaurantResults
        origin={origin}
        result={restaurants.state.status === 'success' ? restaurants.state.data : null}
        loading={restaurants.state.status === 'loading'}
        error={restaurants.state.status === 'error' ? restaurants.state.error : null}
        onRetry={() => runSearch(dish.trim())}
        selectedIndex={selectedIndex}
        onSelect={setSelectedIndex}
      />
    </>
  )
}

export function FoodPage() {
  const [origin, setOrigin] = useState<Place | null>(null)

  return (
    <PageContainer>
      <PageHeader
        title="Ẩm thực"
        description="Món đặc sản theo khu vực của bạn, quán có món đó gần nhất, và khoảng cách trên bản đồ."
      />

      <Card className="space-y-4 p-5">
        <OriginPicker origin={origin} onChange={setOrigin} />
      </Card>

      {origin ? (
        // Keyed so a new origin starts a fresh search instead of showing the old one.
        <RegionSection key={`${origin.lat},${origin.lon}`} origin={origin} />
      ) : (
        <Card className="p-5">
          <p className="text-sm text-fg-muted">
            Chọn nơi bạn đang ở để xem món đặc sản của vùng và tìm quán gần đó.
          </p>
        </Card>
      )}
    </PageContainer>
  )
}
