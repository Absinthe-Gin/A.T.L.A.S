import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import { useAsyncData } from './useAsyncData'

describe('useAsyncData', () => {
  it('starts in the loading state', () => {
    const fetcher = vi.fn(() => new Promise<string>(() => {}))

    const { result } = renderHook(() => useAsyncData(fetcher))

    expect(result.current).toMatchObject({ status: 'loading', data: null, error: null })
  })

  it('exposes the data when the request succeeds', async () => {
    const fetcher = vi.fn().mockResolvedValue({ id: 1 })

    const { result } = renderHook(() => useAsyncData(fetcher))

    await waitFor(() => expect(result.current.status).toBe('success'))
    expect(result.current.data).toEqual({ id: 1 })
    expect(result.current.error).toBeNull()
  })

  it('exposes an ApiError when the request fails', async () => {
    const failure = new ApiError({ kind: 'network', message: 'Mất kết nối' })
    const fetcher = vi.fn().mockRejectedValue(failure)

    const { result } = renderHook(() => useAsyncData(fetcher))

    await waitFor(() => expect(result.current.status).toBe('error'))
    expect(result.current.error).toBe(failure)
    expect(result.current.data).toBeNull()
  })

  it('converts unexpected failures into an ApiError', async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError('boom'))

    const { result } = renderHook(() => useAsyncData(fetcher))

    await waitFor(() => expect(result.current.status).toBe('error'))
    expect(result.current.error).toBeInstanceOf(ApiError)
    expect(result.current.error?.kind).toBe('unknown')
  })

  it('requests again and returns to loading when reload is called', async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValueOnce(new ApiError({ kind: 'server', message: 'Lỗi' }))
      .mockResolvedValueOnce('second')

    const { result } = renderHook(() => useAsyncData(fetcher))
    await waitFor(() => expect(result.current.status).toBe('error'))

    act(() => result.current.reload())

    expect(result.current.status).toBe('loading')
    await waitFor(() => expect(result.current.status).toBe('success'))
    expect(result.current.data).toBe('second')
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('aborts the request and ignores its result after unmount', async () => {
    let resolve: (value: string) => void = () => {}
    let receivedSignal: AbortSignal | undefined
    const fetcher = vi.fn((signal: AbortSignal) => {
      receivedSignal = signal
      return new Promise<string>((done) => {
        resolve = done
      })
    })

    const { result, unmount } = renderHook(() => useAsyncData(fetcher))
    unmount()
    await act(async () => resolve('late'))

    expect(receivedSignal?.aborted).toBe(true)
    expect(result.current.status).toBe('loading')
  })
})
