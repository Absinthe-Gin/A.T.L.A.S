import { useEffect, useState } from 'react'

import { type ApiError, toApiError } from '@/services/api/errors'

import { searchPlaces } from '../api'
import type { GeoPlace } from '../types'

export const MIN_QUERY_LENGTH = 2
/** Wait for the user to stop typing; the backend also keeps OpenStreetMap's one-request-per-second limit. */
export const SEARCH_DELAY_MS = 450

export type PlaceSearchState =
  | { status: 'idle'; places: []; error: null }
  | { status: 'loading'; places: GeoPlace[]; error: null }
  | { status: 'success'; places: GeoPlace[]; error: null }
  | { status: 'error'; places: []; error: ApiError }

const IDLE: PlaceSearchState = { status: 'idle', places: [], error: null }

/** Places matching `query`, searched after a short pause in typing. */
export function usePlaceSearch(query: string): PlaceSearchState {
  const [state, setState] = useState<PlaceSearchState>(IDLE)
  const trimmed = query.trim()
  const active = trimmed.length >= MIN_QUERY_LENGTH

  useEffect(() => {
    if (!active) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setState((current) => ({ status: 'loading', places: current.places, error: null }))
      searchPlaces(trimmed, controller.signal).then(
        (places) => {
          if (!controller.signal.aborted) setState({ status: 'success', places, error: null })
        },
        (error: unknown) => {
          if (!controller.signal.aborted) setState({ status: 'error', places: [], error: toApiError(error) })
        },
      )
    }, SEARCH_DELAY_MS)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [trimmed, active])

  return active ? state : IDLE
}
