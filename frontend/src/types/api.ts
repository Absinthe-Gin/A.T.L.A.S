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
