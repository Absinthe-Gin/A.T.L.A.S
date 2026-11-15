import { useCallback, useEffect, useState } from 'react'

import { type ApiError, toApiError } from '@/services/api/errors'

export type AsyncState<T> =
  | { status: 'loading'; data: null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: null; error: ApiError }

export type AsyncData<T> = AsyncState<T> & {
  /** Request again and show the loading state. */
  reload: () => void
  /** Request again in the background, keeping the current data on screen until the answer arrives. */
  refresh: () => void
}

const LOADING = { status: 'loading', data: null, error: null } as const

/**
 * Load data once on mount and expose loading, success and error states.
 *
 * `fetcher` must be a stable reference (a module-level function or a
 * memoised callback); a new reference triggers a new request.
 */
export function useAsyncData<T>(fetcher: (signal: AbortSignal) => Promise<T>): AsyncData<T> {
  const [state, setState] = useState<AsyncState<T>>(LOADING)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    fetcher(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) {
          setState({ status: 'success', data, error: null })
        }
      },
      (error: unknown) => {
        // A result that arrives after unmount or reload is no longer wanted.
        if (!controller.signal.aborted) {
          setState({ status: 'error', data: null, error: toApiError(error) })
        }
      },
    )

    return () => controller.abort()
  }, [fetcher, attempt])

  const reload = useCallback(() => {
    setState(LOADING)
    setAttempt((current) => current + 1)
  }, [])

  const refresh = useCallback(() => {
    setAttempt((current) => current + 1)
  }, [])

  return { ...state, reload, refresh }
}
