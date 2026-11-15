import { useCallback, useEffect, useRef, useState } from 'react'

import { type ApiError, toApiError } from '@/services/api/errors'

import { getTransport } from '../api'
import type { TransportOptions, TransportQuery } from '../types'

export type TransportState =
  | { status: 'idle'; data: null; error: null }
  | { status: 'loading'; data: null; error: null }
  | { status: 'success'; data: TransportOptions; error: null }
  | { status: 'error'; data: null; error: ApiError }

/** Ways to make a trip, searched when the user asks. A new search cancels the previous one. */
export function useTransport(): { state: TransportState; search: (query: TransportQuery) => void } {
  const [state, setState] = useState<TransportState>({ status: 'idle', data: null, error: null })
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => () => controllerRef.current?.abort(), [])

  const search = useCallback((query: TransportQuery) => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller
    setState({ status: 'loading', data: null, error: null })
    getTransport(query, controller.signal).then(
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
