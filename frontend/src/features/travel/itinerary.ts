import type { ItineraryItem } from './types'

/** Stop numbers shown on the map and in the list: items with a place, in itinerary order. */
export function stopNumbers(items: ItineraryItem[]): Map<string, number> {
  const numbers = new Map<string, number>()
  for (const item of items) {
    if (item.place) numbers.set(item.id, numbers.size + 1)
  }
  return numbers
}
