/**
 * Mirrors `backend/app/modules/travel/schemas.py` and the external data
 * models in `backend/app/infrastructure/{geo,weather,flights}.py`.
 * Dates are ISO strings (`YYYY-MM-DD`), times `HH:MM:SS`.
 */

import type { Place } from '@/features/places'

export type { GeoPlace, Place } from '@/features/places'

// --- Plans -------------------------------------------------------------------

export interface Plan {
  id: string
  title: string
  destination: Place | null
  start_date: string | null
  end_date: string | null
  note: string | null
  item_count: number
  created_at: string
}

export interface ItineraryItem {
  id: string
  title: string
  day: string | null
  start_time: string | null
  place: Place | null
  note: string | null
}

export interface PlanDetail extends Plan {
  items: ItineraryItem[]
}

export interface PlanCreate {
  title: string
  destination: Place | null
  start_date: string | null
  end_date: string | null
  note: string | null
}

export type PlanUpdate = Partial<PlanCreate>

export interface ItemCreate {
  title: string
  day: string | null
  start_time: string | null
  place: Place | null
  note: string | null
}

// --- Weather (Open-Meteo) ----------------------------------------------------

export interface CurrentWeather {
  observed_at: string
  temperature_c: number
  apparent_temperature_c: number
  humidity_percent: number
  wind_speed_kmh: number
  precipitation_mm: number
  weather_code: number
  description: string
}

export interface DailyWeather {
  date: string
  temperature_max_c: number
  temperature_min_c: number
  precipitation_probability_percent: number | null
  weather_code: number
  description: string
}

export interface WeatherForecast {
  latitude: number
  longitude: number
  timezone: string
  current: CurrentWeather
  daily: DailyWeather[]
  source: string
}

// --- Transport ---------------------------------------------------------------

export interface FlightSegment {
  airline: string
  flight_number: string | null
  departure_airport: string
  departure_time: string
  arrival_airport: string
  arrival_time: string
  duration_minutes: number | null
}

export interface FlightOffer {
  /** Whole đồng; Google Flights does not always report a price. */
  price_vnd: number | null
  total_duration_minutes: number | null
  stops: number
  segments: FlightSegment[]
}

/**
 * ok: prices found. not_configured: no SerpApi key on the server.
 * no_airport: no airport near one end. too_close: flying makes no sense.
 * unavailable: the flight provider failed.
 */
export type FlightStatus = 'ok' | 'not_configured' | 'no_airport' | 'too_close' | 'unavailable'

export interface FlightOptions {
  status: FlightStatus
  origin_airport: string | null
  destination_airport: string | null
  offers: FlightOffer[]
  search_url: string | null
  message: string | null
  source: string | null
}

export interface RoadOption {
  status: 'ok' | 'no_route' | 'unavailable'
  distance_km: number | null
  duration_minutes: number | null
  message: string | null
}

/** A booking site the user opens; Atlas has no timetable data from it. */
export interface TransportLink {
  mode: 'flight' | 'train' | 'bus'
  provider: string
  url: string
  hint: string
}

export interface TransportOptions {
  origin: Place
  destination: Place
  travel_date: string
  straight_distance_km: number
  road: RoadOption
  flights: FlightOptions
  ground_links: TransportLink[]
}

export interface TransportQuery {
  origin: Place
  destination: Place
  travel_date: string
  adults: number
}
