import { useCallback, useState } from 'react'

/** Per-browser convenience only; never holds data the app depends on. */
export const SIDEBAR_STORAGE_KEY = 'atlas.sidebar.collapsed'
export const HISTORY_STORAGE_KEY = 'atlas.chat.history.collapsed'

function readStored(key: string): boolean {
  try {
    return window.localStorage.getItem(key) === '1'
  } catch {
    // Private windows and blocked storage throw: fall back to the default.
    return false
  }
}

function writeStored(key: string, collapsed: boolean): void {
  try {
    window.localStorage.setItem(key, collapsed ? '1' : '0')
  } catch {
    // The choice still applies for this visit.
  }
}

/** Whether a desktop column is folded to its icons. Remembered per browser under `storageKey`. */
export function useSidebarCollapsed(storageKey: string = SIDEBAR_STORAGE_KEY): [boolean, () => void] {
  const [collapsed, setCollapsed] = useState(() => readStored(storageKey))

  const toggle = useCallback(() => {
    setCollapsed((current) => {
      const next = !current
      writeStored(storageKey, next)
      return next
    })
  }, [storageKey])

  return [collapsed, toggle]
}
