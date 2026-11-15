import { apiClient } from '@/services/api/client'

import type { ChatRequest, ChatResponse } from './types'

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
