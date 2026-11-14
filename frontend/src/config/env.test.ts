import { describe, expect, it } from 'vitest'

import { readEnv } from './env'

function source(value: string | undefined): ImportMetaEnv {
  return { VITE_API_BASE_URL: value } as ImportMetaEnv
}

describe('readEnv', () => {
  it('returns the API base URL', () => {
    expect(readEnv(source('http://localhost:8000/api/v1'))).toEqual({
      apiBaseUrl: 'http://localhost:8000/api/v1',
    })
  })

  it('removes trailing slashes and surrounding spaces', () => {
    expect(readEnv(source('  http://localhost:8000/api/v1//  ')).apiBaseUrl).toBe(
      'http://localhost:8000/api/v1',
    )
  })

  it.each([undefined, '', '   '])('rejects a missing value (%j)', (value) => {
    expect(() => readEnv(source(value))).toThrow(/VITE_API_BASE_URL/)
  })
})
