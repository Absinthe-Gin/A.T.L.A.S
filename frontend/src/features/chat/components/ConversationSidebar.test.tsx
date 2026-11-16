import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import { deleteConversation, listConversations, renameConversation } from '../api'
import { useConversations } from '../hooks/useConversations'
import type { ConversationSummary } from '../types'
import { ConversationSidebar } from './ConversationSidebar'

vi.mock('../api')

const today = new Date().toISOString()

function summary(id: string, title: string | null): ConversationSummary {
  return { id, title, created_at: today, last_message_at: today }
}

function Harness({ activeId = null, onActiveDeleted = () => {} }: { activeId?: string | null; onActiveDeleted?: () => void }) {
  const conversations = useConversations()
  return (
    <ConversationSidebar
      conversations={conversations}
      activeId={activeId}
      onNewChat={() => {}}
      onActiveDeleted={onActiveDeleted}
    />
  )
}

function FoldedHarness({ activeId, onToggleCollapsed }: { activeId: string | null; onToggleCollapsed: () => void }) {
  const conversations = useConversations()
  return (
    <ConversationSidebar
      conversations={conversations}
      activeId={activeId}
      onNewChat={() => {}}
      onActiveDeleted={() => {}}
      collapsed
      onToggleCollapsed={onToggleCollapsed}
    />
  )
}

function renderSidebar(props: Parameters<typeof Harness>[0] = {}) {
  return render(
    <MemoryRouter>
      <Harness {...props} />
    </MemoryRouter>,
  )
}

describe('ConversationSidebar', () => {
  beforeEach(() => {
    vi.mocked(listConversations)
      .mockReset()
      .mockResolvedValue({ items: [summary('c1', 'Chuyến Huế'), summary('c2', null)], total: 2, limit: 100, offset: 0 })
    vi.mocked(renameConversation).mockReset()
    vi.mocked(deleteConversation).mockReset()
  })

  it('lists conversations grouped by day, linking to each one', async () => {
    renderSidebar({ activeId: 'c1' })

    const today = await screen.findByRole('region', { name: 'Hôm nay' })
    expect(within(today).getByRole('link', { name: 'Chuyến Huế' })).toHaveAttribute('href', '/chat/c1')
    expect(within(today).getByRole('link', { name: 'Cuộc trò chuyện chưa đặt tên' })).toHaveAttribute('href', '/chat/c2')
  })

  it('says when there is no history yet', async () => {
    vi.mocked(listConversations).mockResolvedValue({ items: [], total: 0, limit: 100, offset: 0 })
    renderSidebar()

    expect(await screen.findByText(/Chưa có cuộc trò chuyện nào/)).toBeInTheDocument()
  })

  it('shows a load error with a retry', async () => {
    vi.mocked(listConversations).mockRejectedValueOnce(new ApiError({ kind: 'network', message: 'Mất kết nối.' }))
    const user = userEvent.setup()
    renderSidebar()

    expect(await screen.findByText('Mất kết nối.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Thử lại' }))
    expect(await screen.findByRole('link', { name: 'Chuyến Huế' })).toBeInTheDocument()
  })

  it('renames a conversation', async () => {
    vi.mocked(renameConversation).mockResolvedValue(summary('c1', 'Huế tháng 12'))
    const user = userEvent.setup()
    renderSidebar()
    await screen.findByRole('link', { name: 'Chuyến Huế' })

    await user.click(screen.getByRole('button', { name: 'Đổi tên Chuyến Huế' }))
    const field = screen.getByRole('textbox', { name: 'Tên mới cho Chuyến Huế' })
    await user.clear(field)
    await user.type(field, 'Huế tháng 12{Enter}')

    expect(renameConversation).toHaveBeenCalledWith('c1', 'Huế tháng 12')
    expect(listConversations).toHaveBeenCalledTimes(2)
  })

  it('asks before deleting, and leaves the open conversation when it is deleted', async () => {
    vi.mocked(deleteConversation).mockResolvedValue()
    const onActiveDeleted = vi.fn()
    const user = userEvent.setup()
    renderSidebar({ activeId: 'c1', onActiveDeleted })
    await screen.findByRole('link', { name: 'Chuyến Huế' })

    await user.click(screen.getByRole('button', { name: 'Xóa Chuyến Huế' }))
    expect(deleteConversation).not.toHaveBeenCalled()
    expect(screen.getByText(/Tin nhắn và đề xuất trong đó sẽ mất/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Xóa' }))

    expect(deleteConversation).toHaveBeenCalledWith('c1')
    expect(onActiveDeleted).toHaveBeenCalledOnce()
  })

  it('keeps the conversation when the user changes their mind', async () => {
    const user = userEvent.setup()
    renderSidebar()
    await screen.findByRole('link', { name: 'Chuyến Huế' })

    await user.click(screen.getByRole('button', { name: 'Xóa Chuyến Huế' }))
    await user.click(screen.getByRole('button', { name: 'Giữ lại' }))

    expect(deleteConversation).not.toHaveBeenCalled()
    expect(screen.getByRole('link', { name: 'Chuyến Huế' })).toBeInTheDocument()
  })

  it('folds to one letter per conversation, with the new-chat and unfold buttons', async () => {
    const onToggleCollapsed = vi.fn()
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <FoldedHarness activeId="c1" onToggleCollapsed={onToggleCollapsed} />
      </MemoryRouter>,
    )

    const chuyen = await screen.findByRole('link', { name: 'Chuyến Huế' })
    expect(chuyen).toHaveTextContent('C')
    expect(chuyen).toHaveAttribute('href', '/chat/c1')
    expect(screen.queryByRole('button', { name: /Xóa/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cuộc trò chuyện mới' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Mở rộng lịch sử trò chuyện' }))
    expect(onToggleCollapsed).toHaveBeenCalledOnce()
  })
})
