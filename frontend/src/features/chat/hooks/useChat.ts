import { useCallback, useEffect, useReducer, useRef } from 'react'

import { type ApiError, toApiError } from '@/services/api/errors'

import { sendChatMessage } from '../api'
import type { ChatMessage, ChatResponse } from '../types'

interface ChatState {
  conversationId: string | null
  messages: ChatMessage[]
  isSending: boolean
}

type ChatAction =
  | { type: 'sent'; id: string; content: string }
  | { type: 'replied'; id: string; response: ChatResponse }
  | { type: 'failed'; id: string; error: ApiError }
  | { type: 'removed'; id: string }
  | { type: 'reset' }

const INITIAL_STATE: ChatState = { conversationId: null, messages: [], isSending: false }

function reducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'sent':
      return {
        ...state,
        isSending: true,
        messages: [
          ...state.messages,
          { id: action.id, role: 'user', content: action.content, status: 'pending', error: null },
        ],
      }
    case 'replied':
      return {
        conversationId: action.response.conversation_id,
        isSending: false,
        messages: [
          ...state.messages.map((message) =>
            message.id === action.id && message.role === 'user'
              ? { ...message, status: 'sent' as const }
              : message,
          ),
          {
            id: action.response.message_id,
            role: 'assistant',
            content: action.response.reply,
            intent: action.response.intent,
            toolCalls: action.response.tool_calls,
          },
        ],
      }
    case 'failed':
      return {
        ...state,
        isSending: false,
        messages: state.messages.map((message) =>
          message.id === action.id && message.role === 'user'
            ? { ...message, status: 'failed' as const, error: action.error }
            : message,
        ),
      }
    case 'removed':
      return { ...state, messages: state.messages.filter((message) => message.id !== action.id) }
    case 'reset':
      return INITIAL_STATE
  }
}

let fallbackCounter = 0

function newLocalId(): string {
  // `crypto.randomUUID` needs a secure context; plain-HTTP LAN access is not one.
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  fallbackCounter += 1
  return `local-${Date.now()}-${fallbackCounter}`
}

export interface UseChat {
  conversationId: string | null
  messages: ChatMessage[]
  isSending: boolean
  /** Send a message. Ignored while a reply is pending or when the text is blank. */
  send: (text: string) => void
  /** Send a failed message again. */
  retry: (messageId: string) => void
  /** Start a new conversation. Cancels a pending reply. */
  reset: () => void
}

export function useChat(): UseChat {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE)
  // Updated synchronously, so two sends in the same frame cannot both start.
  const controllerRef = useRef<AbortController | null>(null)
  const conversationIdRef = useRef<string | null>(null)

  useEffect(() => () => controllerRef.current?.abort(), [])

  const send = useCallback((text: string) => {
    const content = text.trim()
    if (!content || controllerRef.current !== null) return

    const id = newLocalId()
    const controller = new AbortController()
    controllerRef.current = controller
    dispatch({ type: 'sent', id, content })

    const settle = (action: ChatAction) => {
      // A reset or unmount cancelled this request; its result is no longer wanted.
      if (controller.signal.aborted) return
      controllerRef.current = null
      dispatch(action)
    }

    sendChatMessage({ message: content, conversation_id: conversationIdRef.current }, controller.signal).then(
      (response) => {
        conversationIdRef.current = response.conversation_id
        settle({ type: 'replied', id, response })
      },
      (error: unknown) => settle({ type: 'failed', id, error: toApiError(error) }),
    )
  }, [])

  const { messages } = state
  const retry = useCallback(
    (messageId: string) => {
      const failed = messages.find(
        (message) => message.id === messageId && message.role === 'user' && message.status === 'failed',
      )
      if (!failed || controllerRef.current !== null) return
      dispatch({ type: 'removed', id: messageId })
      send(failed.content)
    },
    [messages, send],
  )

  const reset = useCallback(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
    conversationIdRef.current = null
    dispatch({ type: 'reset' })
  }, [])

  return { ...state, send, retry, reset }
}
