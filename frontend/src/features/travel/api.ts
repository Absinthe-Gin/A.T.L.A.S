import { apiClient } from '@/services/api/client'
import type { Page } from '@/types/api'

import type {
  ItemCreate,
  ItineraryItem,
  Plan,
  PlanCreate,
  PlanDetail,
  PlanUpdate,
  TransportOptions,
  TransportQuery,
  WeatherForecast,
} from './types'

// --- Plans -------------------------------------------------------------------

export async function listPlans(signal?: AbortSignal): Promise<Page<Plan>> {
  const response = await apiClient.get<Page<Plan>>('/travel/plans', { params: { limit: 100 }, signal })
  return response.data
}

export async function getPlan(id: string, signal?: AbortSignal): Promise<PlanDetail> {
  const response = await apiClient.get<PlanDetail>(`/travel/plans/${id}`, { signal })
  return response.data
}

export async function createPlan(data: PlanCreate): Promise<PlanDetail> {
  const response = await apiClient.post<PlanDetail>('/travel/plans', data)
  return response.data
}

export async function updatePlan(id: string, data: PlanUpdate): Promise<PlanDetail> {
  const response = await apiClient.patch<PlanDetail>(`/travel/plans/${id}`, data)
  return response.data
}

export async function deletePlan(id: string): Promise<void> {
  await apiClient.delete(`/travel/plans/${id}`)
}

export async function addItem(planId: string, data: ItemCreate): Promise<ItineraryItem> {
  const response = await apiClient.post<ItineraryItem>(`/travel/plans/${planId}/items`, data)
  return response.data
}

export async function deleteItem(planId: string, itemId: string): Promise<void> {
  await apiClient.delete(`/travel/plans/${planId}/items/${itemId}`)
}

// --- Live information --------------------------------------------------------

export async function getWeather(lat: number, lon: number, signal?: AbortSignal): Promise<WeatherForecast> {
  const response = await apiClient.get<WeatherForecast>('/travel/weather', { params: { lat, lon, days: 7 }, signal })
  return response.data
}

export async function getTransport(query: TransportQuery, signal?: AbortSignal): Promise<TransportOptions> {
  const response = await apiClient.get<TransportOptions>('/travel/transport', {
    params: {
      origin_name: query.origin.name,
      origin_lat: query.origin.lat,
      origin_lon: query.origin.lon,
      destination_name: query.destination.name,
      destination_lat: query.destination.lat,
      destination_lon: query.destination.lon,
      travel_date: query.travel_date,
      adults: query.adults,
    },
    signal,
  })
  return response.data
}
