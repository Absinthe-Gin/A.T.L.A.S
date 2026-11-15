import type { ApiError } from '@/services/api/errors'

/** Mirrors `ChatRequest` in `backend/app/modules/ai/schemas.py`. */
export interface ChatRequest {
  message: string
  conversation_id: string | null
}

export type ToolCallStatus = 'success' | 'error'

/** Mirrors `ToolCallSummary` in `backend/app/modules/ai/schemas.py`. */
export interface ToolCallSummary {
  name: string
  status: ToolCallStatus
}

/** Mirrors `ChatResponse` in `backend/app/modules/ai/schemas.py`. */
export interface ChatResponse {
  conversation_id: string
  message_id: string
  reply: string
  intent: string
  tool_calls: ToolCallSummary[]
}

/** Backend limit on `ChatRequest.message`. */
export const MESSAGE_MAX_LENGTH = 4000

export type ChatMessage =
  | {
      id: string
      role: 'user'
      content: string
      /** `pending`: waiting for the reply. `failed`: the request failed; can be retried. */
      status: 'pending' | 'sent' | 'failed'
      error: ApiError | null
    }
  | {
      id: string
      role: 'assistant'
      content: string
      intent: string
      toolCalls: ToolCallSummary[]
    }
