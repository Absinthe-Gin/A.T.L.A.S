/**
 * The only place that reads environment variables.
 * Fails at startup with a clear message when configuration is missing.
 */

export interface AppEnv {
  apiBaseUrl: string
  /** Map tile template for Leaflet. OpenStreetMap's tile policy asks for light use and attribution. */
  mapTileUrl: string
  mapAttribution: string
  /** Tiles used when the first server cannot be reached (e.g. openstreetmap.org blocked on the network). */
  mapFallbackTileUrl: string
  mapFallbackAttribution: string
}

const DEFAULT_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const DEFAULT_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
// The German OpenStreetMap community server: same data, another host, no key, light use.
const DEFAULT_FALLBACK_TILE_URL = 'https://tile.openstreetmap.de/{z}/{x}/{y}.png'
const DEFAULT_FALLBACK_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, tiles <a href="https://www.openstreetmap.de">openstreetmap.de</a>'

export function readEnv(source: ImportMetaEnv): AppEnv {
  const apiBaseUrl = source.VITE_API_BASE_URL?.trim()
  if (!apiBaseUrl) {
    throw new Error(
      'Missing VITE_API_BASE_URL. Copy frontend/.env.example to frontend/.env and set it.',
    )
  }
  return {
    apiBaseUrl: apiBaseUrl.replace(/\/+$/, ''),
    mapTileUrl: source.VITE_MAP_TILE_URL?.trim() || DEFAULT_TILE_URL,
    mapAttribution: source.VITE_MAP_ATTRIBUTION?.trim() || DEFAULT_ATTRIBUTION,
    mapFallbackTileUrl: source.VITE_MAP_FALLBACK_TILE_URL?.trim() || DEFAULT_FALLBACK_TILE_URL,
    mapFallbackAttribution: source.VITE_MAP_FALLBACK_ATTRIBUTION?.trim() || DEFAULT_FALLBACK_ATTRIBUTION,
  }
}

export const env: AppEnv = readEnv(import.meta.env)
