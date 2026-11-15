import { IconExternal, IconMapPin, IconUtensils } from '@/components/icons'
import { Badge } from '@/components/ui/Badge'
import { buttonClasses } from '@/components/ui/buttonClasses'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { InlineAlert } from '@/components/ui/InlineAlert'
import { PinMap } from '@/components/map/PinMap'
import type { Place } from '@/features/places'
import type { ApiError } from '@/services/api/errors'
import { formatDistance } from '@/utils/distance'

import { restaurantMarkers } from '../markers'
import type { DishSearchResult, Restaurant } from '../types'

interface RestaurantResultsProps {
  origin: Place | null
  result: DishSearchResult | null
  loading: boolean
  error: ApiError | null
  onRetry: () => void
  /** The restaurant highlighted on the map and in the list, if any. */
  selectedIndex: number | null
  onSelect: (index: number) => void
}

function openingNote(restaurant: Restaurant): string | null {
  return restaurant.opening_hours ? `Giờ mở cửa: ${restaurant.opening_hours}` : null
}

export function RestaurantResults({
  origin,
  result,
  loading,
  error,
  onRetry,
  selectedIndex,
  onSelect,
}: RestaurantResultsProps) {
  if (loading) {
    return (
      <Card className="p-5">
        <div role="status" aria-label="Đang tìm quán" className="space-y-3">
          <div className="h-16 animate-pulse rounded-control bg-surface-2" />
          <div className="h-16 animate-pulse rounded-control bg-surface-2" />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <InlineAlert
        title="Chưa tìm được quán ăn"
        requestId={error.requestId}
        action={
          <button type="button" onClick={onRetry} className={buttonClasses('secondary', 'sm')}>
            Thử lại
          </button>
        }
      >
        {error.message}
      </InlineAlert>
    )
  }

  if (!result) return null

  const restaurants = result.status === 'ok' ? result.restaurants : []
  const markers = restaurantMarkers(origin, restaurants, selectedIndex)

  return (
    <div className="space-y-4" aria-live="polite">
      <Card className="space-y-2 p-5">
        <h2 className="text-lg font-extrabold text-fg">
          Quán có “{result.dish}” trong {formatDistance(result.radius_m / 1000)}
        </h2>
        {result.status !== 'ok' && result.message && <p className="text-sm text-fg-muted">{result.message}</p>}
        {result.status === 'unavailable' && (
          <button type="button" onClick={onRetry} className={buttonClasses('secondary', 'sm')}>
            Thử lại
          </button>
        )}
      </Card>

      {result.status === 'no_results' && (
        <EmptyState icon={<IconUtensils />} title="Chưa có quán nào trong dữ liệu" />
      )}

      {restaurants.length > 0 && (
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
          <ol className="space-y-3">
            {restaurants.map((restaurant, index) => (
              <li key={`${restaurant.osm_type}-${restaurant.osm_id}`}>
                <button
                  type="button"
                  onClick={() => onSelect(index)}
                  aria-pressed={selectedIndex === index}
                  className={`block w-full cursor-pointer rounded-card border bg-surface p-4 text-left shadow-raise transition-[border-color] duration-150 focus-visible:outline-2 focus-visible:outline-ring ${
                    selectedIndex === index ? 'border-primary/60' : 'border-border hover:border-primary/40'
                  }`}
                >
                  <span className="flex items-start gap-3">
                    <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-note-yellow text-xs font-extrabold text-note-yellow-ink">
                      {index + 1}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block font-bold text-fg">{restaurant.name}</span>
                      <span className="mt-1 flex flex-wrap items-center gap-2 text-sm text-fg-muted">
                        <Badge tone="primary">
                          <IconMapPin size={12} /> {formatDistance(restaurant.distance_km)}
                        </Badge>
                        {restaurant.cuisine && <span>{restaurant.cuisine}</span>}
                      </span>
                      {restaurant.address && <span className="mt-1 block text-sm text-fg-subtle">{restaurant.address}</span>}
                      {openingNote(restaurant) && (
                        <span className="mt-1 block text-xs text-fg-subtle">{openingNote(restaurant)}</span>
                      )}
                    </span>
                  </span>
                </button>
                {restaurant.website && (
                  <a
                    href={restaurant.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1.5 inline-flex items-center gap-1 pl-10 text-xs font-semibold text-primary"
                  >
                    Trang web quán <IconExternal size={12} />
                    <span className="sr-only">(mở trang mới)</span>
                  </a>
                )}
              </li>
            ))}
          </ol>
          <PinMap
            markers={markers}
            label={origin ? `Bản đồ quán ${result.dish} quanh ${origin.name}` : `Bản đồ quán ${result.dish}`}
            className="h-80 lg:sticky lg:top-6"
          />
        </div>
      )}

      <p className="text-xs text-fg-subtle">Nguồn: {result.source}. Quán và giờ mở cửa do người đóng góp ghi nhận, có thể chưa đầy đủ.</p>
    </div>
  )
}
