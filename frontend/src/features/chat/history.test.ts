import { describe, expect, it } from 'vitest'

import { conversationTitle, groupConversations, toChatMessages } from './history'
import type { ConversationMessage, ConversationSummary, PendingAction } from './types'

function message(id: string, role: ConversationMessage['role'], at: string): ConversationMessage {
  return { id, role, content: id, created_at: at }
}

function action(id: string, at: string | null): PendingAction {
  return { id, tool_name: 'finance_create_transaction', summary: id, status: 'pending', error_message: null, created_at: at }
}

describe('toChatMessages', () => {
  // The backend returns newest first.
  const stored = [
    message('a2', 'assistant', '2026-11-16T08:05:00Z'),
    message('s1', 'system', '2026-11-16T08:04:00Z'),
    message('u2', 'user', '2026-11-16T08:03:00Z'),
    message('a1', 'assistant', '2026-11-16T08:01:00Z'),
    message('u1', 'user', '2026-11-16T08:00:00Z'),
  ]

  it('puts messages oldest first and keeps system notes', () => {
    expect(toChatMessages(stored, []).map((m) => `${m.role}:${m.id}`)).toEqual([
      'user:u1',
      'assistant:a1',
      'user:u2',
      'system:s1',
      'assistant:a2',
    ])
  })

  it('shows each proposal under the reply written after it', () => {
    const thread = toChatMessages(stored, [action('p1', '2026-11-16T08:00:30Z'), action('p2', '2026-11-16T08:04:30Z')])

    const replies = Object.fromEntries(
      thread.filter((m) => m.role === 'assistant').map((m) => [m.id, m.role === 'assistant' ? m.pendingActions.map((a) => a.id) : []]),
    )
    expect(replies).toEqual({ a1: ['p1'], a2: ['p2'] })
  })

  it('puts a proposal without a later reply under the last reply', () => {
    const thread = toChatMessages(stored, [action('late', '2026-11-16T09:00:00Z'), action('unknown', null)])
    const last = thread.at(-1)

    expect(last?.role === 'assistant' && last.pendingActions.map((a) => a.id)).toEqual(['late', 'unknown'])
  })

  it('marks loaded user messages as sent', () => {
    const first = toChatMessages(stored, [])[0]
    expect(first).toMatchObject({ role: 'user', status: 'sent', error: null })
  })
})

describe('groupConversations', () => {
  const now = new Date(2026, 10, 16, 15, 0)

  function item(id: string, daysAgo: number): ConversationSummary {
    const at = new Date(2026, 10, 16 - daysAgo, 9, 0).toISOString()
    return { id, title: id, created_at: at, last_message_at: at }
  }

  it('groups by today, yesterday, this week, this month and older', () => {
    const groups = groupConversations([item('a', 0), item('b', 1), item('c', 3), item('d', 20), item('e', 90)], now)

    expect(groups.map((g) => [g.label, g.items.map((i) => i.id)])).toEqual([
      ['Hôm nay', ['a']],
      ['Hôm qua', ['b']],
      ['7 ngày qua', ['c']],
      ['30 ngày qua', ['d']],
      ['Cũ hơn', ['e']],
    ])
  })

  it('leaves out empty groups', () => {
    expect(groupConversations([item('a', 0)], now).map((g) => g.label)).toEqual(['Hôm nay'])
  })
})

describe('conversationTitle', () => {
  it('names untitled conversations', () => {
    expect(conversationTitle({ title: null })).toBe('Cuộc trò chuyện chưa đặt tên')
    expect(conversationTitle({ title: '  ' })).toBe('Cuộc trò chuyện chưa đặt tên')
    expect(conversationTitle({ title: 'Chuyến Huế' })).toBe('Chuyến Huế')
  })
})
