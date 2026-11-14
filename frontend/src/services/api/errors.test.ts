import { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { describe, expect, it } from 'vitest'

import { ApiError, toApiError } from './errors'

const config = {} as InternalAxiosRequestConfig

function httpError(status: number, data: unknown, headers: Record<string, string> = {}) {
  const response = { status, data, headers, statusText: '', config } as AxiosResponse
  return new AxiosError('Request failed', 'ERR_BAD_RESPONSE', config, null, response)
}

function envelope(code: string, message: string, details: unknown[] = []) {
  return { error: { code, message, details, request_id: 'req-123' } }
}

describe('toApiError', () => {
  it('reads code, message, details and request id from the error envelope', () => {
    const details = [{ field: 'amount', message: 'Phải lớn hơn 0' }]

    const error = toApiError(httpError(422, envelope('validation_error', 'Sai dữ liệu', details)))

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      kind: 'validation',
      status: 422,
      code: 'validation_error',
      message: 'Sai dữ liệu',
      details,
      requestId: 'req-123',
    })
  })

  it.each([
    [404, 'transaction_not_found', 'not_found'],
    [409, 'conflict', 'conflict'],
    [422, 'budget_exceeded', 'business'],
    [422, 'validation_failed', 'validation'],
    [400, 'bad_request', 'client'],
    [500, 'internal_server_error', 'server'],
    [502, 'external_service_error', 'external'],
    [503, 'external_service_unavailable', 'external'],
    [504, 'external_service_timeout', 'external'],
  ] as const)('maps HTTP %i with code %s to kind %s', (status, code, kind) => {
    expect(toApiError(httpError(status, envelope(code, 'x'))).kind).toBe(kind)
  })

  it('falls back to a default message when the body is not an error envelope', () => {
    const error = toApiError(httpError(500, '<html>Bad gateway</html>'))

    expect(error.kind).toBe('server')
    expect(error.code).toBeNull()
    expect(error.message).toBe('Hệ thống gặp lỗi. Vui lòng thử lại sau.')
    expect(error.details).toEqual([])
  })

  it('uses the response header when the body has no request id', () => {
    const error = toApiError(httpError(500, null, { 'x-request-id': 'from-header' }))

    expect(error.requestId).toBe('from-header')
  })

  it('reports a network error when no response was received', () => {
    const error = toApiError(new AxiosError('Network Error', 'ERR_NETWORK', config))

    expect(error.kind).toBe('network')
    expect(error.status).toBeNull()
  })

  it.each(['ECONNABORTED', 'ETIMEDOUT'])('reports a timeout for axios code %s', (code) => {
    expect(toApiError(new AxiosError('timeout', code, config)).kind).toBe('timeout')
  })

  it('wraps non-HTTP errors and keeps the original as the cause', () => {
    const original = new TypeError('boom')

    const error = toApiError(original)

    expect(error.kind).toBe('unknown')
    expect(error.cause).toBe(original)
  })

  it('returns an existing ApiError unchanged', () => {
    const original = new ApiError({ kind: 'conflict', message: 'x' })

    expect(toApiError(original)).toBe(original)
  })
})
