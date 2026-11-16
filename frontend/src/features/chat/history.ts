import type { ChatMessage, ConversationMessage, ConversationSummary, PendingAction } from './types'

/**
 * Turn stored messages (newest first, as the backend returns them) into the chat
 * thread, oldest first. Each proposal is shown under the first assistant reply
 * written at or after it; proposals with no later reply go under the last one.
 */
export function toChatMessages(newestFirst: ConversationMessage[], actions: PendingAction[]): ChatMessage[] {
  const ordered = [...newestFirst].reverse()
  const replies = ordered.filter((message) => message.role === 'assistant')
  const actionsByReply = new Map<string, PendingAction[]>()

  for (const action of actions) {
    const created = action.created_at ? Date.parse(action.created_at) : Number.NaN
    const reply =
      replies.find((message) => !Number.isNaN(created) && Date.parse(message.created_at) >= created) ??
      replies.at(-1)
    if (!reply) continue
    actionsByReply.set(reply.id, [...(actionsByReply.get(reply.id) ?? []), action])
  }

  return ordered.map((message): ChatMessage => {
    if (message.role === 'user') {
      return { id: message.id, role: 'user', content: message.content, status: 'sent', error: null }
    }
    if (message.role === 'system') {
      return { id: message.id, role: 'system', content: message.content }
    }
    return {
      id: message.id,
      role: 'assistant',
      content: message.content,
      // Stored replies keep no processing details; they are shown only live.
      intent: 'general',
      toolCalls: [],
      pendingActions: actionsByReply.get(message.id) ?? [],
    }
  })
}

export interface ConversationGroup {
  label: string
  items: ConversationSummary[]
}

const DAY_MS = 24 * 60 * 60 * 1000

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
}

/** Group conversations the way people think about time: today, yesterday, this week… */
export function groupConversations(items: ConversationSummary[], now: Date): ConversationGroup[] {
  const today = startOfDay(now)
  const buckets: [string, (time: number) => boolean][] = [
    ['Hôm nay', (time) => time >= today],
    ['Hôm qua', (time) => time >= today - DAY_MS],
    ['7 ngày qua', (time) => time >= today - 7 * DAY_MS],
    ['30 ngày qua', (time) => time >= today - 30 * DAY_MS],
    ['Cũ hơn', () => true],
  ]
  const groups = buckets.map(([label]) => ({ label, items: [] as ConversationSummary[] }))
  for (const item of items) {
    const time = Date.parse(item.last_message_at)
    const index = buckets.findIndex(([, matches]) => matches(time))
    groups[index].items.push(item)
  }
  return groups.filter((group) => group.items.length > 0)
}

/** A readable name when the conversation has no title. */
export function conversationTitle(item: Pick<ConversationSummary, 'title'>): string {
  return item.title?.trim() || 'Cuộc trò chuyện chưa đặt tên'
}
