import { fireEvent, render, screen, within } from '@testing-library/react'
import { StrictMode } from 'react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getHealth } from '@/features/system-status/api'
import { SystemStatusProvider } from '@/features/system-status/SystemStatusProvider'
import type { HealthResponse } from '@/features/system-status/types'
import { ApiError } from '@/services/api/errors'

import { listConversationActions, listMessages, sendChatMessage } from '../api'
import type { ChatResponse } from '../types'
import { ChatPanel } from './ChatPanel'

vi.mock('../api')
vi.mock('@/features/system-status/api')

function health(llm: 'ok' | 'unavailable'): HealthResponse {
  return {
    status: 'ok',
    environment: 'development',
    version: '0.1.0',
    checks: { database: 'ok', llm: { status: llm, provider: 'ollama' } },
  }
}

function reply(overrides: Partial<ChatResponse> = {}): ChatResponse {
  return {
    conversation_id: 'c1',
    message_id: 'm1',
    reply: 'Chào bạn!',
    intent: 'general',
    tool_calls: [],
    pending_actions: [],
    ...overrides,
  }
}

function renderPanel(props: Parameters<typeof ChatPanel>[0] = {}) {
  return render(
    <SystemStatusProvider>
      <ChatPanel {...props} />
    </SystemStatusProvider>,
  )
}

const input = () => screen.getByRole('textbox', { name: 'Tin nhắn' })
const sendButton = () => screen.getByRole('button', { name: 'Gửi tin nhắn' })

describe('ChatPanel', () => {
  beforeEach(() => {
    vi.mocked(sendChatMessage).mockReset()
    vi.mocked(listMessages).mockReset()
    vi.mocked(listConversationActions).mockReset().mockResolvedValue([])
    vi.mocked(getHealth).mockReset().mockResolvedValue(health('ok'))
  })

  it('opens on a welcome with suggestions of what Atlas can do', () => {
    renderPanel()

    expect(screen.getByRole('heading', { name: 'Hôm nay Atlas giúp gì cho bạn?' })).toBeInTheDocument()
    const suggestions = within(screen.getByRole('list', { name: 'Gợi ý' })).getAllByRole('button')
    expect(suggestions.length).toBeGreaterThanOrEqual(4)
    expect(sendButton()).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cuộc trò chuyện mới' })).toBeDisabled()
    expect(input()).toHaveFocus()
  })

  it('sends a suggestion with one click', async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(reply({ reply: 'Món đặc sản Huế là bún bò.' }))
    const user = userEvent.setup()
    renderPanel()

    await user.click(screen.getByRole('button', { name: /Tìm món ngon/ }))

    expect(vi.mocked(sendChatMessage).mock.calls[0]?.[0]).toEqual({
      message: 'Món đặc sản ở Huế là gì?',
      conversation_id: null,
    })
    expect(await screen.findByText('Món đặc sản Huế là bún bò.')).toBeInTheDocument()
  })

  it('sends with Enter, then shows the reply and which data it used', async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(
      reply({
        reply: 'Đã ghi nhận **50.000 ₫**.',
        intent: 'finance',
        tool_calls: [{ name: 'finance_create_transaction', status: 'success' }],
      }),
    )
    const onCreated = vi.fn()
    const onReply = vi.fn()
    const user = userEvent.setup()
    renderPanel({ onConversationCreated: onCreated, onReply })

    await user.type(input(), 'Ghi chi tiêu{Enter}')

    expect(await screen.findByText('50.000 ₫')).toHaveProperty('tagName', 'STRONG')
    expect(screen.getByText('Ghi chi tiêu')).toBeInTheDocument()
    expect(input()).toHaveValue('')
    const sources = screen.getByRole('list', { name: 'Dữ liệu đã dùng' })
    expect(within(sources).getByText('Đã dùng Tài chính')).toHaveAttribute('title', 'finance_create_transaction')
    expect(onCreated).toHaveBeenCalledWith('c1')
    expect(onReply).toHaveBeenCalledOnce()
  })

  it('shows no data sources for a plain reply', async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(reply())
    const user = userEvent.setup()
    renderPanel()

    await user.type(input(), 'Chào{Enter}')

    await screen.findByText('Chào bạn!')
    expect(screen.queryByRole('list', { name: 'Dữ liệu đã dùng' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sao chép câu trả lời' })).toBeInTheDocument()
  })

  it('copies a reply to the clipboard', async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(reply({ reply: 'Nội dung cần chép' }))
    const user = userEvent.setup()
    const writeText = vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue()
    renderPanel()
    await user.type(input(), 'Chào{Enter}')
    await screen.findByText('Nội dung cần chép')

    await user.click(screen.getByRole('button', { name: 'Sao chép câu trả lời' }))

    expect(writeText).toHaveBeenCalledWith('Nội dung cần chép')
    expect(screen.getByRole('button', { name: 'Đã sao chép' })).toBeInTheDocument()
  })

  it('adds a new line with Shift+Enter instead of sending', async () => {
    const user = userEvent.setup()
    renderPanel()

    await user.type(input(), 'dòng một{Shift>}{Enter}{/Shift}dòng hai')

    expect(input()).toHaveValue('dòng một\ndòng hai')
    expect(sendChatMessage).not.toHaveBeenCalled()
  })

  it('does not send when Enter confirms an IME composition', () => {
    renderPanel()
    fireEvent.change(input(), { target: { value: 'tiếng Việt' } })

    fireEvent.keyDown(input(), { key: 'Enter', keyCode: 229 })
    fireEvent.keyDown(input(), { key: 'Enter', isComposing: true })

    expect(sendChatMessage).not.toHaveBeenCalled()
  })

  it('shows a typing indicator and offers to stop while waiting', async () => {
    vi.mocked(sendChatMessage).mockReturnValue(new Promise(() => {}))
    const user = userEvent.setup()
    renderPanel()

    await user.type(input(), 'Chào{Enter}')

    expect(screen.getByText('Atlas đang soạn câu trả lời')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Gửi tin nhắn' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Dừng chờ câu trả lời' }))

    expect(screen.queryByText('Atlas đang soạn câu trả lời')).not.toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Bạn đã dừng chờ câu trả lời')
    expect(screen.getByRole('button', { name: 'Gửi lại' })).toBeEnabled()
  })

  it('shows a failure next to the message and sends it again', async () => {
    vi.mocked(sendChatMessage)
      .mockRejectedValueOnce(new ApiError({ kind: 'external', message: 'Dịch vụ AI không phản hồi.', requestId: 'req-9' }))
      .mockResolvedValueOnce(reply({ reply: 'Đã nhận.' }))
    const user = userEvent.setup()
    renderPanel()

    await user.type(input(), 'Chào{Enter}')
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Dịch vụ AI không phản hồi.')
    expect(alert).toHaveTextContent('req-9')

    await user.click(screen.getByRole('button', { name: 'Gửi lại' }))

    expect(await screen.findByText('Đã nhận.')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getAllByText('Chào')).toHaveLength(1)
  })

  it('warns when the AI is not available, but still allows sending', async () => {
    vi.mocked(getHealth).mockResolvedValue(health('unavailable'))
    const user = userEvent.setup()
    renderPanel()

    expect(await screen.findByText('Trợ lý AI chưa sẵn sàng')).toBeInTheDocument()
    await user.type(input(), 'Chào')
    expect(sendButton()).toBeEnabled()
  })

  it('clears the conversation when starting a new one', async () => {
    vi.mocked(sendChatMessage).mockResolvedValue(reply())
    const user = userEvent.setup()
    renderPanel()
    await user.type(input(), 'Chào{Enter}')
    await screen.findByText('Chào bạn!')

    await user.click(screen.getByRole('button', { name: 'Cuộc trò chuyện mới' }))

    expect(screen.queryByText('Chào bạn!')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Hôm nay Atlas giúp gì cho bạn?' })).toBeInTheDocument()
  })

  it('reopens a saved conversation with its messages and pending proposals', async () => {
    vi.mocked(listMessages).mockResolvedValue({
      items: [
        { id: 'a1', role: 'assistant', content: 'Mình đã đề xuất, bạn xác nhận nhé.', created_at: '2026-11-16T08:00:02Z' },
        { id: 'u1', role: 'user', content: 'Ghi chi 45k ăn phở', created_at: '2026-11-16T08:00:00Z' },
      ],
      total: 2,
      limit: 200,
      offset: 0,
    })
    vi.mocked(listConversationActions).mockResolvedValue([
      {
        id: 'p1',
        tool_name: 'finance_create_transaction',
        summary: 'Ghi chi 45.000 ₫.',
        status: 'pending',
        error_message: null,
        created_at: '2026-11-16T08:00:01Z',
      },
    ])
    vi.mocked(sendChatMessage).mockResolvedValue(reply({ conversation_id: 'c9', reply: 'Tiếp nhé.' }))
    const onCreated = vi.fn()
    const user = userEvent.setup()
    renderPanel({ conversationId: 'c9', title: 'Chi tiêu', onConversationCreated: onCreated })

    expect(screen.getByRole('status', { name: 'Đang tải cuộc trò chuyện' })).toBeInTheDocument()
    expect(await screen.findByText('Ghi chi 45k ăn phở')).toBeInTheDocument()
    expect(screen.getByText('Chi tiêu')).toBeInTheDocument()
    expect(screen.getByText('Ghi chi 45.000 ₫.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xác nhận' })).toBeEnabled()

    await user.type(input(), 'Cảm ơn{Enter}')

    expect(vi.mocked(sendChatMessage).mock.calls[0]?.[0]).toEqual({ message: 'Cảm ơn', conversation_id: 'c9' })
    expect(await screen.findByText('Tiếp nhé.')).toBeInTheDocument()
    expect(onCreated).not.toHaveBeenCalled()
  })

  it('loads a saved conversation under StrictMode, whose effects run twice in development', async () => {
    vi.mocked(listMessages).mockResolvedValue({
      items: [{ id: 'u1', role: 'user', content: 'Thời tiết Đà Lạt?', created_at: '2026-11-16T08:00:00Z' }],
      total: 1,
      limit: 200,
      offset: 0,
    })
    render(
      <StrictMode>
        <SystemStatusProvider>
          <ChatPanel conversationId="c7" />
        </SystemStatusProvider>
      </StrictMode>,
    )

    expect(await screen.findByText('Thời tiết Đà Lạt?')).toBeInTheDocument()
    expect(screen.queryByRole('status', { name: 'Đang tải cuộc trò chuyện' })).not.toBeInTheDocument()
  })

  it('says when a saved conversation no longer exists', async () => {
    vi.mocked(listMessages).mockRejectedValue(
      new ApiError({ kind: 'not_found', status: 404, message: 'Không tìm thấy cuộc hội thoại.' }),
    )
    const onNewChat = vi.fn()
    const user = userEvent.setup()
    renderPanel({ conversationId: 'gone', onNewChat })

    expect(await screen.findByText('Không tìm thấy cuộc trò chuyện này')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Bắt đầu cuộc trò chuyện mới' }))
    expect(onNewChat).toHaveBeenCalledOnce()
  })
})
