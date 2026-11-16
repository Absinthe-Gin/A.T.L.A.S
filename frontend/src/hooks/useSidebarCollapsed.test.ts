import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SIDEBAR_STORAGE_KEY, useSidebarCollapsed } from './useSidebarCollapsed'

describe('useSidebarCollapsed', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('starts expanded when nothing was saved', () => {
    const { result } = renderHook(() => useSidebarCollapsed())

    expect(result.current[0]).toBe(false)
  })

  it('toggles and remembers the choice for the next visit', () => {
    const { result, unmount } = renderHook(() => useSidebarCollapsed())

    act(() => result.current[1]())

    expect(result.current[0]).toBe(true)
    expect(window.localStorage.getItem(SIDEBAR_STORAGE_KEY)).toBe('1')
    unmount()

    const next = renderHook(() => useSidebarCollapsed())
    expect(next.result.current[0]).toBe(true)
  })

  it('still works when storage is blocked', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('blocked')
    })
    const { result } = renderHook(() => useSidebarCollapsed())

    act(() => result.current[1]())

    expect(result.current[0]).toBe(true)
  })
})
