/** Shapes shared by every backend endpoint. Mirrors `app/core/error_handlers.py`. */

export interface ApiErrorDetail {
  field: string | null
  message: string
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details: ApiErrorDetail[]
    request_id: string | null
  }
}

/** One page of a growing list. Mirrors `app/shared/schemas.py`. */
export interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
