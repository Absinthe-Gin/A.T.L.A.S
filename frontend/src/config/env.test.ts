import { describe, expect, it } from 'vitest'

import { readEnv } from './env'

function source(value: string | undefined): ImportMetaEnv {
  return { VITE_API_BASE_URL: value } as ImportMetaEnv
}

describe('readEnv', () => {
  it('returns the API base URL', () => {
    expect(readEnv(source('http://127.0.0.1:8710/api/v1')).apiBaseUrl).toBe('http://127.0.0.1:8710/api/v1')
  })

  it('uses OpenStreetMap tiles unless another tile server is configured', () => {
    expect(readEnv(source('http://x')).mapTileUrl).toBe('https://tile.openstreetmap.org/{z}/{x}/{y}.png')
    expect(readEnv(source('http://x')).mapAttribution).toContain('OpenStreetMap')
    const custom = { VITE_API_BASE_URL: 'http://x', VITE_MAP_TILE_URL: 'https://tiles.test/{z}/{x}/{y}.png' }
    expect(readEnv(custom as ImportMetaEnv).mapTileUrl).toBe('https://tiles.test/{z}/{x}/{y}.png')
  })

  it('falls back to the openstreetmap.de tile server, which carries the same OpenStreetMap data', () => {
    const env = readEnv(source('http://x'))
    expect(env.mapFallbackTileUrl).toBe('https://tile.openstreetmap.de/{z}/{x}/{y}.png')
    expect(env.mapFallbackAttribution).toContain('openstreetmap.de')
    expect(env.mapFallbackAttribution).toContain('OpenStreetMap')
  })

  it('removes trailing slashes and surrounding spaces', () => {
    expect(readEnv(source('  http://127.0.0.1:8710/api/v1//  ')).apiBaseUrl).toBe(
      'http://127.0.0.1:8710/api/v1',
    )
  })

  it.each([undefined, '', '   '])('rejects a missing value (%j)', (value) => {
    expect(() => readEnv(source(value))).toThrow(/VITE_API_BASE_URL/)
  })
})
