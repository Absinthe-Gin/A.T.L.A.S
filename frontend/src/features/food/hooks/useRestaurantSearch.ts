import { useCallback, useEffect, useRef, useState } from 'react'

import { type ApiError, toApiError } from '@/services/api/errors'

import { findRestaurants, type RestaurantQuery } from '../api'
import type { DishSearchResult } from '../types'

export type RestaurantSearchState =
  | { status: 'idle'; data: null; error: null }
  | { status: 'loading'; data: null; error: null }
  | { status: 'success'; data: DishSearchResult; error: null }
  | { status: 'error'; data: null; error: ApiError }

/** Restaurants for a dish, searched when the user asks. A new search cancels the previous one. */
export function useRestaurantSearch(): { state: RestaurantSearchState; search: (query: RestaurantQuery) => void } {
  const [state, setState] = useState<RestaurantSearchState>({ status: 'idle', data: null, error: null })
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => () => controllerRef.current?.abort(), [])

  const search = useCallback((query: RestaurantQuery) => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller
    setState({ status: 'loading', data: null, error: null })
    findRestaurants(query, controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setState({ status: 'success', data, error: null })
      },
      (error: unknown) => {
        if (!controller.signal.aborted) setState({ status: 'error', data: null, error: toApiError(error) })
      },
    )
  }, [])

  return { state, search }
}
