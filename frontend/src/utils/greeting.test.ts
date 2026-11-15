import { describe, expect, it } from 'vitest'

import { greeting } from './greeting'

describe('greeting', () => {
  it.each([
    [4, 'Chào buổi sáng.'],
    [10, 'Chào buổi sáng.'],
    [11, 'Chào buổi trưa.'],
    [12, 'Chào buổi trưa.'],
    [13, 'Chào buổi chiều.'],
    [17, 'Chào buổi chiều.'],
    [18, 'Chào buổi tối.'],
    [23, 'Chào buổi tối.'],
    [0, 'Chào buổi tối.'],
    [3, 'Chào buổi tối.'],
  ])('greets at %i:00 with "%s"', (hour, expected) => {
    expect(greeting(new Date(2026, 10, 15, hour, 30))).toBe(expected)
  })
})
