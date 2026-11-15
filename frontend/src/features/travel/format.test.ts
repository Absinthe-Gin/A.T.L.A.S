import { describe, expect, it } from 'vitest'

import { daysBetween, formatDate, formatDateRange, formatDistance, formatDuration, formatTime } from './format'
import { stopNumbers } from './itinerary'

describe('travel formatting', () => {
  it('formats dates as calendar days', () => {
    expect(formatDate('2026-12-01')).toBe('01/12/2026')
    expect(formatDateRange('2026-12-01', '2026-12-03')).toBe('01/12/2026 – 03/12/2026')
    expect(formatDateRange('2026-12-01', '2026-12-01')).toBe('01/12/2026')
    expect(formatDateRange(null, null)).toBeNull()
    expect(formatTime('08:30:00')).toBe('08:30')
  })

  it.each([
    [45, '45 phút'],
    [60, '1 giờ'],
    [150, '2 giờ 30 phút'],
  ])('formats %i minutes', (minutes, text) => {
    expect(formatDuration(minutes)).toBe(text)
  })

  it('rounds long distances and keeps a decimal for short ones', () => {
    expect(formatDistance(1480.2)).toBe('1.480 km')
    expect(formatDistance(3.4)).toBe('3,4 km')
  })

  it('lists every day of a plan, across month ends', () => {
    expect(daysBetween('2026-11-30', '2026-12-02')).toEqual(['2026-11-30', '2026-12-01', '2026-12-02'])
    expect(daysBetween('2026-12-01', null)).toEqual([])
  })

  it('numbers only the itinerary items that have a place', () => {
    const place = { name: 'A', lat: 1, lon: 1 }
    const items = [
      { id: 'a', title: 'A', day: null, start_time: null, place, note: null },
      { id: 'b', title: 'B', day: null, start_time: null, place: null, note: null },
      { id: 'c', title: 'C', day: null, start_time: null, place, note: null },
    ]
    expect([...stopNumbers(items)]).toEqual([
      ['a', 1],
      ['c', 2],
    ])
  })
})
