import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import { confirmAction, sendChatMessage } from '../api'
import type { ChatResponse } from '../types'
import { useChat } from './useChat'

vi.mock('../api')

function reply(overrides: Partial<ChatResponse> = {}): ChatResponse {
  return {
    conversation_id: 'conv-1',
    message_id: 'msg-1',
    reply: 'Chào bạn!',
    intent: 'general',
    tool_calls: [],
    pending_actions: [],
    ...overrides,
  }
}

/** A request whose outcome the test decides later. */
function deferred() {
  let resolve: (value: ChatResponse) => void = () => {}
  let reject: (error: unknown) => void = () => {}
  const promise = new Promise<ChatResponse>((done, fail) => {
    resolve = done
    reject = fail
  })
  return { promise, resolve, reject }
}

describe('useChat', () => {
  beforeEach(() => {
    vi.mocked(sendChatMessage).mockReset()
  })

  it('shows the user message at once and the reply when it arrives', async () => {
    const request = deferred()
    vi.mocked(sendChatMessage).mockReturnValue(request.promise)
    const { result } = renderHook(() => useChat())

    act(() => result.current.send('  Xin chào  '))

    expect(result.current.isSending).toBe(true)
    expect(result.current.messages).toMatchObject([{ role: 'user', content: 'Xin chào', status: 'pending' }])

    await act(async () => request.resolve(reply()))

    expect(result.current.isSending).toBe(false)
    expect(result.current.conversationId).toBe('conv-1')
    expect(result.current.messages).toMatchObject([
      { role: 'user', status: 'sent' },
      { role: 'assistant', id: 'msg-1', content: 'Chào bạn!', intent: 'general' },
    ])
    expect(sendChatMessage).toHaveBeenCalledWith(
      { message: 'Xin chào', conversation_id: null },
      expect.any(AbortSignal),
    )
  })

  it('continues the same conversation on the next message', async () => {
    vi.mocked(sendChatMessage)
      .mockResolvedValueOnce(reply())
      .mockResolvedValueOnce(reply({ message_id: 'msg-2' }))
    const { result } = renderHook(() => useChat())

    act(() => result.current.send('một'))
    await waitFor(() => expect(result.current.isSending).toBe(false))
    act(() => result.current.send('hai'))
    await waitFor(() => expect(result.current.messages).toHaveLength(4))

    expect(vi.mocked(sendChatMessage).mock.calls[1]?.[0]).toEqual({
      message: 'hai',
      conversation_id: 'conv-1',
    })
  })

  it.each(['', '   ', '\n'])('ignores a blank message (%j)', (text) => {
    const { result } = renderHook(() => useChat())

    act(() => result.current.send(text))

    expect(result.current.messages).toEqual([])
    expect(sendChatMessage).not.toHaveBeenCalled()
  })

  it('ignores a second message while a reply is pending', () => {
    vi.mocked(sendChatMessage).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useChat())

    act(() => {
      result.current.send('một')
      result.current.send('hai')
    })

    expect(sendChatMessage).toHaveBeenCalledTimes(1)
    expect(result.current.messages).toHaveLength(1)
  })

  it('marks the message as failed and keeps the error', async () => {
    const error = new ApiError({ kind: 'external', message: 'AI không phản hồi', requestId: 'r1' })
    vi.mocked(sendChatMessage).mockRejectedValue(error)
    const { result } = renderHook(() => useChat())

    act(() => result.current.send('Chào'))
    await waitFor(() => expect(result.current.isSending).toBe(false))

    expect(result.current.messages).toMatchObject([{ role: 'user', status: 'failed', error }])
  })

  it('sends a failed message again on retry, without duplicating it', async () => {
    vi.mocked(sendChatMessage)
      .mockRejectedValueOnce(new ApiError({ kind: 'network', message: 'Mất kết nối' }))
      .mockResolvedValueOnce(reply())
    const { result } = renderHook(() => useChat())
    act(() => result.current.send('Chào'))
    await waitFor(() => expect(result.current.isSending).toBe(false))
    const failedId = result.current.messages[0]?.id ?? ''

    act(() => result.current.retry(failedId))
    await waitFor(() => expect(result.current.messages).toHaveLength(2))

    expect(result.current.messages).toMatchObject([
      { role: 'user', content: 'Chào', status: 'sent' },
      { role: 'assistant', content: 'Chào bạn!' },
    ])
    expect(sendChatMessage).toHaveBeenCalledTimes(2)
  })

  it('starts over on reset and ignores the cancelled reply', async () => {
    const request = deferred()
    vi.mocked(sendChatMessage).mockReturnValue(request.promise)
    const { result } = renderHook(() => useChat())
    act(() => result.current.send('Chào'))
    const signal = vi.mocked(sendChatMessage).mock.calls[0]?.[1]

    act(() => result.current.reset())
    await act(async () => request.resolve(reply()))

    expect(signal?.aborted).toBe(true)
    expect(result.current.messages).toEqual([])
    expect(result.current.conversationId).toBeNull()
    expect(result.current.isSending).toBe(false)
  })

  it('aborts the pending request on unmount', () => {
    vi.mocked(sendChatMessage).mockReturnValue(new Promise(() => {}))
    const { result, unmount } = renderHook(() => useChat())
    act(() => result.current.send('Chào'))
    const signal = vi.mocked(sendChatMessage).mock.calls[0]?.[1]

    unmount()

    expect(signal?.aborted).toBe(true)
  })
})

describe('useChat proposals', () => {
  beforeEach(() => {
    vi.mocked(sendChatMessage).mockReset()
    vi.mocked(confirmAction).mockReset()
  })

  it('keeps proposals with the reply and updates them once resolved', async () => {
    const proposal = { id: 'a1', tool_name: 'x', summary: 'Ghi chi 50.000 ₫.', status: 'pending' as const, error_message: null }
    vi.mocked(sendChatMessage).mockResolvedValue(reply({ pending_actions: [proposal] }))
    vi.mocked(confirmAction).mockResolvedValue({ ...proposal, status: 'confirmed' })
    const { result } = renderHook(() => useChat())
    act(() => result.current.send('Ghi chi 50k'))
    await waitFor(() => expect(result.current.messages).toHaveLength(2))

    let error: unknown = 'unset'
    await act(async () => {
      error = await result.current.resolveAction('a1', 'confirm')
    })

    expect(error).toBeNull()
    expect(result.current.messages[1]).toMatchObject({ pendingActions: [{ id: 'a1', status: 'confirmed' }] })
  })

  it('returns the error and leaves the proposal pending when resolving fails', async () => {
    const proposal = { id: 'a1', tool_name: 'x', summary: 's', status: 'pending' as const, error_message: null }
    vi.mocked(sendChatMessage).mockResolvedValue(reply({ pending_actions: [proposal] }))
    vi.mocked(confirmAction).mockRejectedValue(new ApiError({ kind: 'network', message: 'Mất kết nối' }))
    const { result } = renderHook(() => useChat())
    act(() => result.current.send('Ghi'))
    await waitFor(() => expect(result.current.messages).toHaveLength(2))

    let error: ApiError | null = null
    await act(async () => {
      error = await result.current.resolveAction('a1', 'confirm')
    })

    expect(error).toBeInstanceOf(ApiError)
    expect(result.current.messages[1]).toMatchObject({ pendingActions: [{ status: 'pending' }] })
  })
})
