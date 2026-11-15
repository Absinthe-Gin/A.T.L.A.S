import { apiClient } from '@/services/api/client'

import type { ChatRequest, ChatResponse, PendingAction } from './types'

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
