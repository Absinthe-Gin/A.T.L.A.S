import { apiClient } from '@/services/api/client'

import type { Page } from '@/types/api'

import type { ChatRequest, ChatResponse, ConversationMessage, ConversationSummary, PendingAction } from './types'

/**
 * A reply can take a while on a local model. Longer than the backend's
 * default LLM_TIMEOUT_SECONDS (60), so the backend reports a timeout first.
 */
export const CHAT_TIMEOUT_MS = 90_000

export async function sendChatMessage(
  request: ChatRequest,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>('/chat', request, {
    signal,
    timeout: CHAT_TIMEOUT_MS,
  })
  return response.data
}

/** Carry out a change the assistant proposed. The returned status says whether it succeeded. */
export async function confirmAction(id: string): Promise<PendingAction> {
  const response = await apiClient.post<PendingAction>(`/chat/actions/${id}/confirm`)
  return response.data
}

export async function cancelAction(id: string): Promise<PendingAction> {
  const response = await apiClient.post<PendingAction>(`/chat/actions/${id}/cancel`)
  return response.data
}

// --- History -------------------------------------------------------------------

/** Most recently active conversations first. */
export async function listConversations(signal?: AbortSignal): Promise<Page<ConversationSummary>> {
  const response = await apiClient.get<Page<ConversationSummary>>('/conversations', {
    params: { limit: 100 },
    signal,
  })
  return response.data
}

/** The latest messages of a conversation, newest first (backend order). */
export async function listMessages(conversationId: string, signal?: AbortSignal): Promise<Page<ConversationMessage>> {
  const response = await apiClient.get<Page<ConversationMessage>>(`/conversations/${conversationId}/messages`, {
    params: { limit: 200 },
    signal,
  })
  return response.data
}

export async function listConversationActions(conversationId: string, signal?: AbortSignal): Promise<PendingAction[]> {
  const response = await apiClient.get<PendingAction[]>(`/chat/conversations/${conversationId}/actions`, { signal })
  return response.data
}

export async function renameConversation(conversationId: string, title: string): Promise<ConversationSummary> {
  const response = await apiClient.patch<ConversationSummary>(`/conversations/${conversationId}`, { title })
  return response.data
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiClient.delete(`/conversations/${conversationId}`)
}
