import L from 'leaflet'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { addTilesWithFallback } from './tiles'

const sources = {
  primary: { url: 'https://primary.test/{z}/{x}/{y}.png', attribution: 'Primary' },
  fallback: { url: 'https://fallback.test/{z}/{x}/{y}.png', attribution: 'Fallback' },
}

describe('addTilesWithFallback', () => {
  let container: HTMLDivElement
  let map: L.Map

  beforeEach(() => {
    container = document.createElement('div')
    document.body.append(container)
    map = L.map(container).setView([16, 106], 5)
  })

  afterEach(() => {
    map.remove()
    container.remove()
  })

  it('shows the primary tiles while they load', () => {
    const tiles = addTilesWithFallback(map, sources)

    expect(tiles.current().getAttribution?.()).toBe('Primary')
    expect(map.hasLayer(tiles.current())).toBe(true)
  })

  it('switches to the fallback once when a primary tile fails', () => {
    const tiles = addTilesWithFallback(map, sources)
    const primary = tiles.current()

    primary.fire('tileerror')
    primary.fire('tileerror')

    expect(map.hasLayer(primary)).toBe(false)
    expect(tiles.current()).not.toBe(primary)
    expect(tiles.current().getAttribution?.()).toBe('Fallback')
    expect(map.hasLayer(tiles.current())).toBe(true)
  })
})
