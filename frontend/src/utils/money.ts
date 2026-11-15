/** Money is whole đồng (integers) end to end; these helpers never use fractional đồng. */

const VND = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 })
const GROUPED = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 })

/** `1250000` → `"1.250.000 ₫"`. */
export function formatVnd(amount: number): string {
  return VND.format(amount)
}

/** `1250000` → `"1.250.000"` (no currency sign), for compact tables. */
export function formatGrouped(amount: number): string {
  return GROUPED.format(amount)
}

const MULTIPLIERS: Record<string, number> = { k: 1_000, tr: 1_000_000, m: 1_000_000 }

/**
 * Read an amount typed the way people write it in Vietnamese:
 * `"50000"`, `"50.000"`, `"50 000"`, `"50k"`, `"1tr"`, `"1,5tr"`, `"-20k"`.
 * Returns whole đồng, or `null` when the text is not an amount.
 */
export function parseAmount(input: string): number | null {
  const text = input.trim().toLowerCase().replace(/[.\s₫đ]/g, '')
  const match = /^(-)?(\d+)(?:,(\d{1,3}))?(k|tr|m)?$/.exec(text)
  if (!match) return null

  const [, sign, whole, fraction = '', suffix] = match
  const multiplier = suffix ? (MULTIPLIERS[suffix] ?? 1) : 1
  // A decimal part only makes sense with a suffix: "1,5tr" = 1 500 000 đ.
  if (fraction && multiplier === 1) return null

  const scale = 10 ** fraction.length
  const fractionValue = fraction ? (Number(fraction) * multiplier) / scale : 0
  if (!Number.isInteger(fractionValue)) return null

  const value = Number(whole) * multiplier + fractionValue
  if (!Number.isSafeInteger(value)) return null
  return sign ? -value : value
}

/** `"2026-11"` for the month containing `date`. */
export function toMonth(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

/** `shiftMonth("2026-12", 1)` → `"2027-01"`. */
export function shiftMonth(month: string, delta: number): string {
  const [year, monthIndex] = month.split('-').map(Number)
  return toMonth(new Date(year ?? 1970, (monthIndex ?? 1) - 1 + delta, 1))
}

/** `"2026-11"` → `"Tháng 11/2026"`. */
export function formatMonth(month: string): string {
  const [year, monthNumber] = month.split('-')
  return `Tháng ${Number(monthNumber)}/${year}`
}

/** Local calendar date as `YYYY-MM-DD` (not UTC, so late evenings stay on the right day). */
export function toIsoDate(date: Date): string {
  return `${toMonth(date)}-${String(date.getDate()).padStart(2, '0')}`
}

/** `"2026-11-15"` → `"Thứ bảy, 15/11"`. */
export function formatDay(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  const date = new Date(year ?? 1970, (month ?? 1) - 1, day ?? 1)
  const weekday = new Intl.DateTimeFormat('vi-VN', { weekday: 'long' }).format(date)
  return `${weekday.charAt(0).toUpperCase()}${weekday.slice(1)}, ${String(day).padStart(2, '0')}/${String(month).padStart(2, '0')}`
}
