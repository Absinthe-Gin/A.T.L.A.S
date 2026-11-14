import { isAxiosError } from 'axios'

import type { ApiErrorBody, ApiErrorDetail } from '@/types/api'

export type ApiErrorKind =
  | 'validation'
  | 'not_found'
  | 'conflict'
  | 'business'
  | 'client'
  | 'external'
  | 'server'
  | 'network'
  | 'timeout'
  | 'unknown'

interface ApiErrorInit {
  kind: ApiErrorKind
  message: string
  status?: number | null
  code?: string | null
  details?: ApiErrorDetail[]
  requestId?: string | null
  cause?: unknown
}

/** The single error type the rest of the app receives from the API layer. */
export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly code: string | null
  readonly details: ApiErrorDetail[]
  readonly requestId: string | null

  constructor(init: ApiErrorInit) {
    super(init.message, { cause: init.cause })
    this.name = 'ApiError'
    this.kind = init.kind
    this.status = init.status ?? null
    this.code = init.code ?? null
    this.details = init.details ?? []
    this.requestId = init.requestId ?? null
  }
}

const DEFAULT_MESSAGES: Record<ApiErrorKind, string> = {
  validation: 'Dữ liệu không hợp lệ.',
  not_found: 'Không tìm thấy dữ liệu yêu cầu.',
  conflict: 'Yêu cầu xung đột với dữ liệu hiện tại.',
  business: 'Yêu cầu không thể thực hiện.',
  client: 'Yêu cầu không hợp lệ.',
  external: 'Dịch vụ bên ngoài đang gặp sự cố. Vui lòng thử lại sau.',
  server: 'Hệ thống gặp lỗi. Vui lòng thử lại sau.',
  network: 'Không kết nối được tới máy chủ. Hãy kiểm tra Backend đã chạy chưa.',
  timeout: 'Máy chủ phản hồi quá lâu. Vui lòng thử lại.',
  unknown: 'Đã xảy ra lỗi không xác định.',
}

const VALIDATION_CODES = new Set(['validation_error', 'validation_failed'])
const TIMEOUT_CODES = new Set(['ECONNABORTED', 'ETIMEDOUT'])

function isApiErrorBody(data: unknown): data is ApiErrorBody {
  if (typeof data !== 'object' || data === null || !('error' in data)) {
    return false
  }
  const error = (data as { error: unknown }).error
  return (
    typeof error === 'object' &&
    error !== null &&
    typeof (error as { code?: unknown }).code === 'string' &&
    typeof (error as { message?: unknown }).message === 'string'
  )
}

function kindFromStatus(status: number, code: string | null): ApiErrorKind {
  if (status === 404) return 'not_found'
  if (status === 409) return 'conflict'
  if (status === 422) {
    return code !== null && VALIDATION_CODES.has(code) ? 'validation' : 'business'
  }
  if (status === 502 || status === 503 || status === 504) return 'external'
  if (status >= 500) return 'server'
  return 'client'
}

/** Convert anything thrown by the HTTP layer into an `ApiError`. */
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error
  }

  if (!isAxiosError(error)) {
    return new ApiError({ kind: 'unknown', message: DEFAULT_MESSAGES.unknown, cause: error })
  }

  const response = error.response
  if (!response) {
    const kind: ApiErrorKind =
      error.code !== undefined && TIMEOUT_CODES.has(error.code) ? 'timeout' : 'network'
    return new ApiError({ kind, message: DEFAULT_MESSAGES[kind], cause: error })
  }

  const body = isApiErrorBody(response.data) ? response.data.error : null
  const headerRequestId: unknown = response.headers?.['x-request-id']
  const kind = kindFromStatus(response.status, body?.code ?? null)

  return new ApiError({
    kind,
    status: response.status,
    code: body?.code ?? null,
    message: body?.message || DEFAULT_MESSAGES[kind],
    details: Array.isArray(body?.details) ? body.details : [],
    requestId: body?.request_id ?? (typeof headerRequestId === 'string' ? headerRequestId : null),
    cause: error,
  })
}
