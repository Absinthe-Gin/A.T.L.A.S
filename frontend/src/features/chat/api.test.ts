import { describe, expect, it, vi } from 'vitest'

import { apiClient } from '@/services/api/client'

import { CHAT_TIMEOUT_MS, sendChatMessage } from './api'

describe('sendChatMessage', () => {
  it('posts the message with a timeout long enough for a local model', async () => {
    const response = {
      conversation_id: 'c1',
      message_id: 'm1',
      reply: 'Chào',
      intent: 'general',
      tool_calls: [],
    }
    vi.spyOn(apiClient, 'post').mockResolvedValue({ data: response })
    const controller = new AbortController()

    const result = await sendChatMessage({ message: 'Chào', conversation_id: null }, controller.signal)

    expect(result).toEqual(response)
    expect(apiClient.post).toHaveBeenCalledWith(
      '/chat',
      { message: 'Chào', conversation_id: null },
      { signal: controller.signal, timeout: CHAT_TIMEOUT_MS },
    )
    // Longer than the backend's default LLM timeout (60 s), so the backend answers first.
    expect(CHAT_TIMEOUT_MS).toBeGreaterThan(60_000)
  })
})
