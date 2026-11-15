import L from 'leaflet'

export interface TileSource {
  url: string
  attribution: string
}

/**
 * Add the primary tile layer; if its tiles fail to load, replace it once with the
 * fallback. Some networks block openstreetmap.org while other hosts work.
 * Returns the layer currently shown, for tests and callers that need it.
 */
export function addTilesWithFallback(
  map: L.Map,
  sources: { primary: TileSource; fallback: TileSource },
): { current: () => L.TileLayer } {
  let current = L.tileLayer(sources.primary.url, { attribution: sources.primary.attribution, maxZoom: 19 })
  let switched = false

  current.on('tileerror', () => {
    if (switched) return
    switched = true
    map.removeLayer(current)
    current = L.tileLayer(sources.fallback.url, { attribution: sources.fallback.attribution, maxZoom: 19 })
    current.addTo(map)
  })
  current.addTo(map)

  return { current: () => current }
}
