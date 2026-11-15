import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { THEME_STORAGE_KEY, useTheme } from './useTheme'

describe('useTheme', () => {
  afterEach(() => {
    delete document.documentElement.dataset.theme
    localStorage.clear()
  })

  it('starts from the theme applied by index.html', () => {
    document.documentElement.dataset.theme = 'dark'

    const { result } = renderHook(() => useTheme())

    expect(result.current.theme).toBe('dark')
  })

  it('toggles the document theme and remembers the choice', () => {
    document.documentElement.dataset.theme = 'light'
    const { result } = renderHook(() => useTheme())

    act(() => result.current.toggleTheme())

    expect(result.current.theme).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
  })

  it('cross-fades colours only while switching', () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useTheme())

    act(() => result.current.toggleTheme())
    expect(document.documentElement).toHaveClass('theme-switching')

    act(() => vi.advanceTimersByTime(300))
    expect(document.documentElement).not.toHaveClass('theme-switching')
    vi.useRealTimers()
  })

  it('still switches theme when storage is unavailable', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    const { result } = renderHook(() => useTheme())

    act(() => result.current.toggleTheme())

    expect(document.documentElement.dataset.theme).toBe('dark')
  })
})
