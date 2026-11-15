/** Display helpers for travel data. Pure functions; Vietnamese wording. */

export { formatDistance } from '@/utils/distance'

const DAY_FORMAT = new Intl.DateTimeFormat('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit' })
const DATE_FORMAT = new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })

/** `YYYY-MM-DD` read as a calendar day, not shifted by the browser's time zone. */
function calendarDay(isoDate: string): Date {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(year, month - 1, day)
}

/** `2026-12-01` → `01/12/2026`. */
export function formatDate(isoDate: string): string {
  return DATE_FORMAT.format(calendarDay(isoDate))
}

/** `2026-12-01` → `Th 3, 01/12`. */
export function formatWeekday(isoDate: string): string {
  return DAY_FORMAT.format(calendarDay(isoDate))
}

export function formatDateRange(start: string | null, end: string | null): string | null {
  if (start && end) return start === end ? formatDate(start) : `${formatDate(start)} – ${formatDate(end)}`
  if (start) return `Từ ${formatDate(start)}`
  if (end) return `Đến ${formatDate(end)}`
  return null
}

/** `08:30:00` → `08:30`. */
export function formatTime(time: string): string {
  return time.slice(0, 5)
}

/** `150` → `2 giờ 30 phút`. */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours === 0) return `${rest} phút`
  return rest === 0 ? `${hours} giờ` : `${hours} giờ ${rest} phút`
}

/** Every day from start to end, inclusive. Empty when the plan has no complete date range. */
export function daysBetween(start: string | null, end: string | null): string[] {
  if (!start || !end) return []
  const days: string[] = []
  const cursor = calendarDay(start)
  const last = calendarDay(end)
  while (cursor <= last && days.length < 60) {
    const month = String(cursor.getMonth() + 1).padStart(2, '0')
    const day = String(cursor.getDate()).padStart(2, '0')
    days.push(`${cursor.getFullYear()}-${month}-${day}`)
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
}
