/** Mirrors `HealthResponse` in `backend/app/modules/health/schemas.py`. */

export type HealthStatus = 'ok' | 'degraded'
export type CheckStatus = 'ok' | 'error'
export type LlmStatus = 'ok' | 'unavailable'

export interface HealthResponse {
  status: HealthStatus
  environment: string
  version: string
  checks: {
    database: CheckStatus
    /** Informational: only chat depends on the LLM. */
    llm: {
      status: LlmStatus
      provider: string
    }
  }
}
