import { useCallback, useState } from 'react'

export type Theme = 'light' | 'dark'

/** Must match the inline script in index.html. */
export const THEME_STORAGE_KEY = 'atlas-theme'

/** How long colours cross-fade when the theme changes (matches index.css). */
const SWITCH_DURATION_MS = 260

let switchTimer: ReturnType<typeof setTimeout> | undefined

function currentTheme(): Theme {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

/**
 * The active colour theme. The initial value is applied by index.html before
 * first paint (saved choice, otherwise the system preference).
 */
export function useTheme(): { theme: Theme; toggleTheme: () => void } {
  const [theme, setTheme] = useState<Theme>(currentTheme)

  const toggleTheme = useCallback(() => {
    const root = document.documentElement
    const next: Theme = currentTheme() === 'dark' ? 'light' : 'dark'

    // Cross-fade only during an explicit switch, never on first paint.
    root.classList.add('theme-switching')
    clearTimeout(switchTimer)
    switchTimer = setTimeout(() => root.classList.remove('theme-switching'), SWITCH_DURATION_MS)

    root.dataset.theme = next
    try {
      localStorage.setItem(THEME_STORAGE_KEY, next)
    } catch {
      // Storage can be unavailable (private mode); the theme still applies for this visit.
    }
    setTheme(next)
  }, [])

  return { theme, toggleTheme }
}
