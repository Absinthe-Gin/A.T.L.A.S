import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getHealth } from '@/features/system-status/api'
import { SystemStatusProvider } from '@/features/system-status/SystemStatusProvider'
import type { HealthResponse } from '@/features/system-status/types'
import { ApiError } from '@/services/api/errors'

import { sendChatMessage } from '../api'
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

function renderPanel() {
  return render(
    <SystemStatusProvider>
      <ChatPanel />
    </SystemStatusProvider>,
  )
}

const input = () => screen.getByRole('textbox', { name: 'Tin nhắn' })
const sendButton = () => screen.getByRole('button', { name: 'Gửi tin nhắn' })

describe('ChatPanel', () => {
  beforeEach(() => {
    vi.mocked(sendChatMessage).mockReset()
    vi.mocked(getHealth).mockReset().mockResolvedValue(health('ok'))
  })

  it('starts empty and states what the assistant can do today', () => {
    renderPanel()

    expect(screen.getByRole('heading', { name: 'Bắt đầu trò chuyện' })).toBeInTheDocument()
    expect(screen.getByText(/trợ lý chỉ trò chuyện/)).toBeInTheDocument()
    expect(sendButton()).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cuộc trò chuyện mới' })).toBeDisabled()
  })

  it('sends with Enter, then shows the reply with its processing details', async () => {
    vi.mocked(sendChatMessage).mockResolvedValue({
      conversation_id: '3f2a9c1e-0000-0000-0000-000000000000',
      message_id: 'm1',
      reply: 'Đã ghi nhận.',
      intent: 'finance',
      tool_calls: [{ name: 'finance_create_transaction', status: 'success' }],
    })
    const user = userEvent.setup()
    renderPanel()

    await user.type(input(), 'Ghi chi tiêu{Enter}')

    expect(await screen.findByText('Đã ghi nhận.')).toBeInTheDocument()
    expect(screen.getByText('Ghi chi tiêu')).toBeInTheDocument()
    expect(input()).toHaveValue('')
    const details = screen.getByLabelText('Chi tiết xử lý')
    expect(within(details).getByText('finance')).toBeInTheDocument()
    expect(within(details).getByText('finance_create_transaction')).toBeInTheDocument()
    expect(within(details).getByText('(thành công)')).toBeInTheDocument()
    expect(screen.getByText('3f2a9c1e')).toBeInTheDocument()
  })

  it('hides processing details for a plain reply', async () => {
    vi.mocked(sendChatMessage).mockResolvedValue({
      conversation_id: 'c1',
      message_id: 'm1',
      reply: 'Chào bạn!',
      intent: 'general',
      tool_calls: [],
    })
    const user = userEvent.setup()
    renderPanel()

    await user.type(input(), 'Chào{Enter}')

    await screen.findByText('Chào bạn!')
    expect(screen.queryByLabelText('Chi tiết xử lý')).not.toBeInTheDocument()
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

  it('shows a typing indicator and blocks sending while waiting', async () => {
    vi.mocked(sendChatMessage).mockReturnValue(new Promise(() => {}))
    const user = userEvent.setup()
    renderPanel()

    await user.type(input(), 'Chào{Enter}')
    await user.type(input(), 'Tiếp')

    expect(screen.getByText('Trợ lý đang soạn câu trả lời')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Đang gửi' })).toBeDisabled()
  })

  it('shows a failure next to the message and sends it again', async () => {
    vi.mocked(sendChatMessage)
      .mockRejectedValueOnce(
        new ApiError({ kind: 'external', message: 'Dịch vụ AI không phản hồi.', requestId: 'req-9' }),
      )
      .mockResolvedValueOnce({
        conversation_id: 'c1',
        message_id: 'm1',
        reply: 'Đã nhận.',
        intent: 'general',
        tool_calls: [],
      })
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
    vi.mocked(sendChatMessage).mockResolvedValue({
      conversation_id: 'c1',
      message_id: 'm1',
      reply: 'Chào bạn!',
      intent: 'general',
      tool_calls: [],
    })
    const user = userEvent.setup()
    renderPanel()
    await user.type(input(), 'Chào{Enter}')
    await screen.findByText('Chào bạn!')

    await user.click(screen.getByRole('button', { name: 'Cuộc trò chuyện mới' }))

    expect(screen.queryByText('Chào bạn!')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Bắt đầu trò chuyện' })).toBeInTheDocument()
  })
})
