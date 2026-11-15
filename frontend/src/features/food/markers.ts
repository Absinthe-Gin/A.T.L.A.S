import type { MapMarker } from '@/components/map/PinMap'
import type { Place } from '@/features/places'

import type { Restaurant } from './types'

/** Markers for the map: the user's origin, then each restaurant numbered by distance. */
export function restaurantMarkers(origin: Place | null, restaurants: Restaurant[], selected: number | null): MapMarker[] {
  const markers: MapMarker[] = []
  if (origin) markers.push({ id: 'origin', place: origin, kind: 'selected' })
  restaurants.forEach((restaurant, index) => {
    markers.push({
      id: `restaurant-${restaurant.osm_type}-${restaurant.osm_id}`,
      place: { name: restaurant.name, lat: restaurant.lat, lon: restaurant.lon },
      kind: selected === index ? 'selected' : 'stop',
      badge: String(index + 1),
    })
  })
  return markers
}
