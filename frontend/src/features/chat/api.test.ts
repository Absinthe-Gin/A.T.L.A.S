import { describe, expect, it, vi } from 'vitest'

import { apiClient } from '@/services/api/client'

import {
  CHAT_TIMEOUT_MS,
  deleteConversation,
  listConversationActions,
  listConversations,
  listMessages,
  renameConversation,
  sendChatMessage,
} from './api'

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

describe('conversation history', () => {
  it('reads the list, the messages and the proposals of a conversation', async () => {
    vi.restoreAllMocks()
    vi.spyOn(apiClient, 'get').mockResolvedValue({ data: 'body' })

    await listConversations()
    await listMessages('c1')
    await listConversationActions('c1')

    expect(vi.mocked(apiClient.get).mock.calls.map((call) => [call[0], call[1]?.params])).toEqual([
      ['/conversations', { limit: 100 }],
      ['/conversations/c1/messages', { limit: 200 }],
      ['/chat/conversations/c1/actions', undefined],
    ])
  })

  it('renames and deletes a conversation', async () => {
    vi.restoreAllMocks()
    vi.spyOn(apiClient, 'patch').mockResolvedValue({ data: 'renamed' })
    vi.spyOn(apiClient, 'delete').mockResolvedValue({ data: undefined })

    await expect(renameConversation('c1', 'Huế')).resolves.toBe('renamed')
    await deleteConversation('c1')

    expect(apiClient.patch).toHaveBeenCalledWith('/conversations/c1', { title: 'Huế' })
    expect(apiClient.delete).toHaveBeenCalledWith('/conversations/c1')
  })
})
