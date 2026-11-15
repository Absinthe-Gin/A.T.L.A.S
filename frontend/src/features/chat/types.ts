import type { ApiError } from '@/services/api/errors'

/** Mirrors `ChatRequest` in `backend/app/modules/ai/schemas.py`. */
export interface ChatRequest {
  message: string
  conversation_id: string | null
}

export type ToolCallStatus = 'success' | 'error' | 'pending'

/** Mirrors `ToolCallSummary` in `backend/app/modules/ai/schemas.py`. */
export interface ToolCallSummary {
  name: string
  status: ToolCallStatus
}

export type PendingActionStatus = 'pending' | 'confirmed' | 'cancelled' | 'failed'

/** A change the assistant proposed. Mirrors `PendingActionView` in `backend/app/modules/ai/schemas.py`. */
export interface PendingAction {
  id: string
  tool_name: string
  summary: string
  status: PendingActionStatus
  error_message: string | null
}

/** Mirrors `ChatResponse` in `backend/app/modules/ai/schemas.py`. */
export interface ChatResponse {
  conversation_id: string
  message_id: string
  reply: string
  intent: string
  tool_calls: ToolCallSummary[]
  pending_actions: PendingAction[]
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
      pendingActions: PendingAction[]
    }
