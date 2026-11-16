import { useCallback, useEffect, useReducer, useRef } from 'react'

import { ApiError, toApiError } from '@/services/api/errors'

import { cancelAction, confirmAction, listConversationActions, listMessages, sendChatMessage } from '../api'
import { toChatMessages } from '../history'
import type { ChatMessage, ChatResponse, PendingAction } from '../types'

/** `idle`: a new chat. `loading` / `error`: reading a saved conversation. `ready`: shown. */
export type HistoryStatus = 'idle' | 'loading' | 'error' | 'ready'

interface ChatState {
  conversationId: string | null
  messages: ChatMessage[]
  isSending: boolean
  history: HistoryStatus
  historyError: ApiError | null
}

type ChatAction =
  | { type: 'sent'; id: string; content: string }
  | { type: 'replied'; id: string; response: ChatResponse }
  | { type: 'failed'; id: string; error: ApiError }
  | { type: 'removed'; id: string }
  | { type: 'actionResolved'; action: PendingAction }
  | { type: 'historyLoading'; conversationId: string }
  | { type: 'historyLoaded'; conversationId: string; messages: ChatMessage[] }
  | { type: 'historyFailed'; error: ApiError }
  | { type: 'reset' }

const INITIAL_STATE: ChatState = {
  conversationId: null,
  messages: [],
  isSending: false,
  history: 'idle',
  historyError: null,
}

/** Shown on a message whose reply the user stopped waiting for. */
export const STOPPED_ERROR = new ApiError({
  kind: 'unknown',
  message: 'Bạn đã dừng chờ câu trả lời. Gửi lại để hỏi tiếp.',
})

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
        ...state,
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
            pendingActions: action.response.pending_actions ?? [],
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
    case 'actionResolved':
      return {
        ...state,
        messages: state.messages.map((message) =>
          message.role === 'assistant' && message.pendingActions.some((item) => item.id === action.action.id)
            ? {
                ...message,
                pendingActions: message.pendingActions.map((item) =>
                  item.id === action.action.id ? action.action : item,
                ),
              }
            : message,
        ),
      }
    case 'removed':
      return { ...state, messages: state.messages.filter((message) => message.id !== action.id) }
    case 'historyLoading':
      return { ...INITIAL_STATE, conversationId: action.conversationId, history: 'loading' }
    case 'historyLoaded':
      return { ...INITIAL_STATE, conversationId: action.conversationId, messages: action.messages, history: 'ready' }
    case 'historyFailed':
      return { ...state, history: 'error', historyError: action.error }
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

export interface UseChatOptions {
  /** Called when the first reply of a new conversation gives it an ID. */
  onConversationCreated?: (conversationId: string) => void
  /** Called after every reply, e.g. to refresh the conversation list. */
  onReply?: () => void
}

export interface UseChat {
  conversationId: string | null
  messages: ChatMessage[]
  isSending: boolean
  history: HistoryStatus
  historyError: ApiError | null
  /** Send a message. Ignored while a reply is pending or when the text is blank. */
  send: (text: string) => void
  /** Send a failed message again. */
  retry: (messageId: string) => void
  /** Stop waiting for the current reply. The message can be sent again. */
  stop: () => void
  /** Start a new conversation. Cancels a pending reply. */
  reset: () => void
  /** Read the saved conversation again after a failure. */
  reloadHistory: () => void
  /** Confirm or cancel a proposed change. Resolves to the error to show, or null. */
  resolveAction: (id: string, decision: 'confirm' | 'cancel') => Promise<ApiError | null>
}

/**
 * The chat thread. With `conversationId`, the saved conversation is loaded first;
 * with `null`, a new conversation starts. Changing it switches conversations.
 */
export function useChat(conversationId: string | null = null, options: UseChatOptions = {}): UseChat {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE)
  // Updated synchronously, so two sends in the same frame cannot both start.
  const controllerRef = useRef<AbortController | null>(null)
  const pendingMessageRef = useRef<string | null>(null)
  const conversationIdRef = useRef<string | null>(null)
  const historyControllerRef = useRef<AbortController | null>(null)
  const optionsRef = useRef(options)
  useEffect(() => {
    optionsRef.current = options
  })

  useEffect(
    () => () => {
      controllerRef.current?.abort()
      historyControllerRef.current?.abort()
      // The aborted load never finished: forget the conversation so that mounting
      // again (React StrictMode does this in development) loads it again.
      controllerRef.current = null
      conversationIdRef.current = null
    },
    [],
  )

  const loadHistory = useCallback((id: string) => {
    historyControllerRef.current?.abort()
    controllerRef.current?.abort()
    controllerRef.current = null
    const controller = new AbortController()
    historyControllerRef.current = controller
    conversationIdRef.current = id
    dispatch({ type: 'historyLoading', conversationId: id })
    Promise.all([listMessages(id, controller.signal), listConversationActions(id, controller.signal)]).then(
      ([page, actions]) => {
        if (!controller.signal.aborted) {
          dispatch({ type: 'historyLoaded', conversationId: id, messages: toChatMessages(page.items, actions) })
        }
      },
      (error: unknown) => {
        if (!controller.signal.aborted) dispatch({ type: 'historyFailed', error: toApiError(error) })
      },
    )
  }, [])

  // Follow the requested conversation. A conversation this hook just created is
  // already on screen, so it is not loaded again.
  useEffect(() => {
    if (conversationId === conversationIdRef.current) return
    if (conversationId === null) {
      historyControllerRef.current?.abort()
      controllerRef.current?.abort()
      controllerRef.current = null
      conversationIdRef.current = null
      dispatch({ type: 'reset' })
      return
    }
    loadHistory(conversationId)
  }, [conversationId, loadHistory])

  const send = useCallback((text: string) => {
    const content = text.trim()
    if (!content || controllerRef.current !== null) return

    const id = newLocalId()
    const controller = new AbortController()
    controllerRef.current = controller
    pendingMessageRef.current = id
    dispatch({ type: 'sent', id, content })

    const settle = (action: ChatAction) => {
      // A reset, stop or unmount cancelled this request; its result is no longer wanted.
      if (controller.signal.aborted) return
      controllerRef.current = null
      pendingMessageRef.current = null
      dispatch(action)
    }

    const startedNew = conversationIdRef.current === null
    sendChatMessage({ message: content, conversation_id: conversationIdRef.current }, controller.signal).then(
      (response) => {
        if (controller.signal.aborted) return
        conversationIdRef.current = response.conversation_id
        settle({ type: 'replied', id, response })
        if (startedNew) optionsRef.current.onConversationCreated?.(response.conversation_id)
        optionsRef.current.onReply?.()
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

  const stop = useCallback(() => {
    const controller = controllerRef.current
    const messageId = pendingMessageRef.current
    if (!controller || !messageId) return
    controller.abort()
    controllerRef.current = null
    pendingMessageRef.current = null
    dispatch({ type: 'failed', id: messageId, error: STOPPED_ERROR })
  }, [])

  const reset = useCallback(() => {
    historyControllerRef.current?.abort()
    controllerRef.current?.abort()
    controllerRef.current = null
    pendingMessageRef.current = null
    conversationIdRef.current = null
    dispatch({ type: 'reset' })
  }, [])

  const reloadHistory = useCallback(() => {
    if (conversationIdRef.current) loadHistory(conversationIdRef.current)
  }, [loadHistory])

  const resolveAction = useCallback(async (id: string, decision: 'confirm' | 'cancel') => {
    try {
      const resolved = await (decision === 'confirm' ? confirmAction(id) : cancelAction(id))
      dispatch({ type: 'actionResolved', action: resolved })
      return null
    } catch (error) {
      return toApiError(error)
    }
  }, [])

  return { ...state, send, retry, stop, reset, reloadHistory, resolveAction }
}
