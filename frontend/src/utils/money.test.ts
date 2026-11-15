import { describe, expect, it } from 'vitest'

import { formatDay, formatMonth, formatVnd, parseAmount, shiftMonth, toIsoDate, toMonth } from './money'

describe('parseAmount', () => {
  it.each([
    ['50000', 50_000],
    ['50.000', 50_000],
    ['50 000', 50_000],
    ['1.250.000', 1_250_000],
    ['50k', 50_000],
    ['50K', 50_000],
    ['1tr', 1_000_000],
    ['1,5tr', 1_500_000],
    ['2,25tr', 2_250_000],
    ['1,5k', 1_500],
    ['3m', 3_000_000],
    ['45.000đ', 45_000],
    ['45.000 ₫', 45_000],
    ['-20k', -20_000],
    ['0', 0],
    ['1', 1],
  ])('reads %j as %i đồng', (input, expected) => {
    expect(parseAmount(input)).toBe(expected)
  })

  it.each(['', '   ', 'abc', '12a', '1,5', '1,2345tr', '--5', '5-', '1,0005k', '99999999999999999999'])(
    'rejects %j',
    (input) => {
      expect(parseAmount(input)).toBeNull()
    },
  )
})

describe('formatVnd', () => {
  it('uses Vietnamese grouping and the đồng sign', () => {
    expect(formatVnd(1_250_000).replace(/\s/g, ' ')).toBe('1.250.000 ₫')
    expect(formatVnd(0).replace(/\s/g, ' ')).toBe('0 ₫')
  })
})

describe('months and days', () => {
  it('moves across year boundaries', () => {
    expect(shiftMonth('2026-12', 1)).toBe('2027-01')
    expect(shiftMonth('2026-01', -1)).toBe('2025-12')
    expect(shiftMonth('2026-05', 0)).toBe('2026-05')
  })

  it('formats months and local dates', () => {
    expect(formatMonth('2026-11')).toBe('Tháng 11/2026')
    expect(toMonth(new Date(2026, 0, 31))).toBe('2026-01')
    // Late evening stays on the local calendar day.
    expect(toIsoDate(new Date(2026, 10, 15, 23, 59))).toBe('2026-11-15')
  })

  it('names the weekday of a date', () => {
    expect(formatDay('2026-11-15')).toMatch(/^Chủ nhật, 15\/11$/i)
  })
})
