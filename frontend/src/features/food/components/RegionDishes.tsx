import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { IconUtensils } from '@/components/icons'
import { formatDistance } from '@/utils/distance'

import type { RegionRecommendation } from '../types'

interface RegionDishesProps {
  recommendation: RegionRecommendation
  /** Searches restaurants for a dish name. */
  onSearchDish: (dish: string) => void
  disabled: boolean
}

/** The specialties of the region nearest the user. Each dish can be searched. */
export function RegionDishes({ recommendation, onSearchDish, disabled }: RegionDishesProps) {
  return (
    <Card aria-labelledby="region-heading" className="space-y-4 p-5">
      <div>
        <h2 id="region-heading" className="text-lg font-extrabold text-fg">
          Món đặc sản {recommendation.region}
        </h2>
        <p className="mt-1 text-sm text-fg-muted">
          Gần nhất với {recommendation.reference_city}, cách {formatDistance(recommendation.distance_to_reference_km)}.
        </p>
      </div>

      {recommendation.dishes.length === 0 ? (
        <EmptyState icon={<IconUtensils />} title="Chưa có món gợi ý cho khu vực này" />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {recommendation.dishes.map((dish) => (
            <li key={dish.name}>
              <button
                type="button"
                disabled={disabled}
                onClick={() => onSearchDish(dish.name)}
                className="block h-full w-full cursor-pointer rounded-control border border-border bg-surface-2/50 p-3 text-left transition-[border-color,translate] duration-150 hover:-translate-y-0.5 hover:border-primary/40 focus-visible:outline-2 focus-visible:outline-ring disabled:cursor-not-allowed disabled:opacity-60"
              >
                <span className="block font-bold text-fg">{dish.name}</span>
                <span className="mt-1 block text-sm text-fg-muted">{dish.description}</span>
                <span className="mt-2 block text-xs font-semibold text-primary">Tìm quán gần đây</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <p className="text-xs text-fg-subtle">{recommendation.note}</p>
    </Card>
  )
}
