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
  /** ISO time; used to show a proposal under the reply it belongs to when a chat is reopened. */
  created_at?: string | null
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
  | {
      /** A note from the system, e.g. that a proposal was confirmed. */
      id: string
      role: 'system'
      content: string
    }

/** One entry of the conversation list. Mirrors `ConversationSummary` in `backend/app/modules/memory/schemas.py`. */
export interface ConversationSummary {
  id: string
  title: string | null
  created_at: string
  last_message_at: string
}

/** A stored message. Mirrors `ConversationMessage` in `backend/app/modules/memory/schemas.py`. */
export interface ConversationMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}
