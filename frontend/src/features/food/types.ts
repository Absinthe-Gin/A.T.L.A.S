/**
 * Mirrors `backend/app/modules/food/schemas.py`. Distances are kilometres from the
 * origin the user chose; the backend computes them.
 */

export interface DishSuggestion {
  name: string
  description: string
}

/** The region nearest the user's place, with its editorial specialties. */
export interface RegionRecommendation {
  region: string
  reference_city: string
  distance_to_reference_km: number
  dishes: DishSuggestion[]
  note: string
}

export interface Restaurant {
  name: string
  cuisine: string | null
  address: string | null
  opening_hours: string | null
  phone: string | null
  website: string | null
  lat: number
  lon: number
  distance_km: number
  osm_type: string
  osm_id: number
}

/** ok: restaurants found. no_results: none mapped with that name. unavailable: the data source failed. */
export type DishSearchStatus = 'ok' | 'no_results' | 'unavailable'

export interface DishSearchResult {
  dish: string
  radius_m: number
  status: DishSearchStatus
  restaurants: Restaurant[]
  message: string | null
  source: string
}

/** Search radius choices, in metres. The backend accepts 100 m to 20 km. */
export const RADIUS_OPTIONS_M = [1000, 3000, 5000, 10000] as const
export type RadiusM = (typeof RADIUS_OPTIONS_M)[number]
