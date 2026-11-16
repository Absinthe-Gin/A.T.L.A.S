import { type ReactNode, useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

import { IconArrowDown, IconPlus } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { InlineAlert } from '@/components/ui/InlineAlert'
import { useSystemStatus } from '@/features/system-status/context'
import { isAiReady } from '@/features/system-status/status'

import { useChat } from '../hooks/useChat'
import { ChatComposer } from './ChatComposer'
import { ChatMessageItem, TypingIndicator } from './ChatMessageItem'
import { ChatWelcome } from './ChatWelcome'

/** Within this distance of the bottom, the thread follows new messages. */
const STICK_TO_BOTTOM_PX = 80

function AiUnavailableNotice({ onRecheck }: { onRecheck: () => void }) {
  return (
    <InlineAlert
      tone="warning"
      title="Trợ lý AI chưa sẵn sàng"
      action={
        <Button variant="secondary" size="sm" onClick={onRecheck}>
          Kiểm tra lại
        </Button>
      }
    >
      Atlas chưa kết nối được tới mô hình AI (Ollama). Mở Ollama rồi bấm Kiểm tra lại. Bạn vẫn có thể gửi tin nhắn để thử.
    </InlineAlert>
  )
}

interface ChatPanelProps {
  /** The saved conversation to open; `null` starts a new one. */
  conversationId?: string | null
  /** The conversation's title, when known (from the history list). */
  title?: string | null
  onConversationCreated?: (conversationId: string) => void
  /** After every reply, e.g. to refresh the history list. */
  onReply?: () => void
  /** "New conversation" pressed. Without it, the panel clears itself. */
  onNewChat?: () => void
  /** Shown at the start of the header, e.g. the button that opens the history on mobile. */
  headerStart?: ReactNode
}

export function ChatPanel({
  conversationId = null,
  title = null,
  onConversationCreated,
  onReply,
  onNewChat,
  headerStart,
}: ChatPanelProps) {
  const chat = useChat(conversationId, { onConversationCreated, onReply })
  const health = useSystemStatus()
  const aiReady = isAiReady(health)
  const threadRef = useRef<HTMLDivElement>(null)
  // Read while rendering the button; the ref is read by effects without re-running them.
  const [atBottom, setAtBottom] = useState(true)
  const atBottomRef = useRef(true)
  const isNewChat = chat.messages.length === 0 && chat.history === 'idle'

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'auto') => {
    const thread = threadRef.current
    if (!thread) return
    if (typeof thread.scrollTo === 'function') thread.scrollTo({ top: thread.scrollHeight, behavior })
    else thread.scrollTop = thread.scrollHeight
  }, [])

  // Follow new messages, unless the user scrolled up to read something earlier.
  useLayoutEffect(() => {
    if (atBottomRef.current) scrollToBottom()
  }, [chat.messages.length, chat.isSending, scrollToBottom])

  // A conversation that just loaded opens at its end.
  useEffect(() => {
    if (chat.history === 'ready') {
      atBottomRef.current = true
      scrollToBottom()
    }
  }, [chat.history, scrollToBottom])

  const handleScroll = () => {
    const thread = threadRef.current
    if (!thread) return
    const near = thread.scrollHeight - thread.scrollTop - thread.clientHeight < STICK_TO_BOTTOM_PX
    atBottomRef.current = near
    setAtBottom(near)
  }

  const startNewChat = onNewChat ?? chat.reset
  const notice = aiReady === false ? <AiUnavailableNotice onRecheck={health.reload} /> : null

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="flex items-center gap-2 border-b border-border bg-chrome/90 px-3 py-2.5 backdrop-blur sm:px-5">
        {headerStart}
        <div className="min-w-0 flex-1">
          <h1 className="text-base font-extrabold text-fg">Trợ lý AI</h1>
          <p className="truncate text-xs text-fg-subtle">{title?.trim() || 'Cuộc trò chuyện mới'}</p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          icon={<IconPlus size={16} />}
          onClick={startNewChat}
          disabled={isNewChat}
        >
          {/* Icon only on narrow screens; the name stays available to screen readers. */}
          <span className="sr-only sm:not-sr-only">Cuộc trò chuyện mới</span>
        </Button>
      </header>

      {isNewChat ? (
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          {notice && <div className="mx-auto w-full max-w-2xl px-4 pt-4">{notice}</div>}
          <ChatWelcome onPick={chat.send} disabled={chat.isSending}>
            <ChatComposer onSend={chat.send} onStop={chat.stop} isSending={chat.isSending} autoFocus />
          </ChatWelcome>
        </div>
      ) : (
        <>
          <div className="relative min-h-0 flex-1">
            <div ref={threadRef} onScroll={handleScroll} className="h-full overflow-y-auto px-4 py-6 sm:px-6">
              <div className="mx-auto w-full max-w-3xl space-y-6">
                {notice}

                {chat.history === 'loading' && (
                  <div role="status" aria-label="Đang tải cuộc trò chuyện" className="space-y-6">
                    <div className="ml-auto h-12 w-2/3 animate-pulse rounded-bubble bg-surface-2" />
                    <div className="h-24 w-5/6 animate-pulse rounded-card bg-surface-2" />
                    <div className="ml-auto h-10 w-1/2 animate-pulse rounded-bubble bg-surface-2" />
                  </div>
                )}

                {chat.history === 'error' && chat.historyError && (
                  <InlineAlert
                    title={
                      chat.historyError.status === 404
                        ? 'Không tìm thấy cuộc trò chuyện này'
                        : 'Không tải được cuộc trò chuyện'
                    }
                    requestId={chat.historyError.requestId}
                    action={
                      chat.historyError.status === 404 ? (
                        <Button variant="secondary" size="sm" onClick={startNewChat}>
                          Bắt đầu cuộc trò chuyện mới
                        </Button>
                      ) : (
                        <Button variant="secondary" size="sm" onClick={chat.reloadHistory}>
                          Thử lại
                        </Button>
                      )
                    }
                  >
                    {chat.historyError.message}
                  </InlineAlert>
                )}

                {chat.messages.length > 0 && (
                  <ol aria-label="Nội dung cuộc trò chuyện" aria-live="polite" className="space-y-7">
                    {chat.messages.map((message) => (
                      <ChatMessageItem
                        key={message.id}
                        message={message}
                        onRetry={chat.retry}
                        onResolveAction={chat.resolveAction}
                        retryDisabled={chat.isSending}
                      />
                    ))}
                    {chat.isSending && <TypingIndicator />}
                  </ol>
                )}
              </div>
            </div>

            {!atBottom && (
              <button
                type="button"
                onClick={() => scrollToBottom('smooth')}
                aria-label="Cuộn xuống tin nhắn mới nhất"
                className="absolute bottom-3 left-1/2 inline-flex size-10 -translate-x-1/2 animate-pop cursor-pointer items-center justify-center rounded-full border border-border-strong bg-surface text-fg shadow-lift transition-colors hover:bg-surface-2"
              >
                <IconArrowDown size={18} />
              </button>
            )}
          </div>

          <div className="bg-gradient-to-t from-bg via-bg to-transparent px-4 pt-2 pb-3 sm:px-6">
            <div className="mx-auto w-full max-w-3xl">
              <ChatComposer
                onSend={chat.send}
                onStop={chat.stop}
                isSending={chat.isSending}
                autoFocus={chat.history !== 'loading'}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
