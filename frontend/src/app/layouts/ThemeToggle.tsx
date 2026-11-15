import { IconMoon, IconSun } from '@/components/icons'
import { IconButton } from '@/components/ui/IconButton'
import { useTheme } from '@/hooks/useTheme'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <IconButton
      label={isDark ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
      // Keyed by theme so the new icon turns in each time the theme changes.
      icon={
        <span key={theme} className="animate-icon-in">
          {isDark ? <IconSun size={18} /> : <IconMoon size={18} />}
        </span>
      }
      onClick={toggleTheme}
    />
  )
}
