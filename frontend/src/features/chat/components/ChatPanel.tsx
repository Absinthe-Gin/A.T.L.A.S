import { useEffect, useRef } from 'react'

import { IconChat, IconInfo, IconPlus } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { InlineAlert } from '@/components/ui/InlineAlert'
import { useSystemStatus } from '@/features/system-status/context'
import { isAiReady } from '@/features/system-status/status'

import { useChat } from '../hooks/useChat'
import { ChatComposer } from './ChatComposer'
import { ChatMessageItem, TypingIndicator } from './ChatMessageItem'

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
      Backend không kết nối được tới mô hình AI. Kiểm tra Ollama đã chạy và <code className="font-mono">OLLAMA_MODEL</code>{' '}
      đã được đặt trong <code className="font-mono">backend/.env</code>. Bạn vẫn có thể gửi tin nhắn để thử.
    </InlineAlert>
  )
}

export function ChatPanel() {
  const chat = useChat()
  const health = useSystemStatus()
  const aiReady = isAiReady(health)
  const threadRef = useRef<HTMLDivElement>(null)
  const isEmpty = chat.messages.length === 0

  // Keep the latest message in view.
  useEffect(() => {
    const thread = threadRef.current
    if (thread) thread.scrollTop = thread.scrollHeight
  }, [chat.messages.length, chat.isSending])

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between gap-4 border-b border-border bg-chrome/90 px-4 py-3 backdrop-blur sm:px-6">
        <div className="min-w-0">
          <h1 className="text-xl font-extrabold text-fg">Trợ lý AI</h1>
          <p className="truncate text-xs text-fg-subtle">
            {chat.conversationId ? (
              <>
                Mã hội thoại <span className="font-mono">{chat.conversationId.slice(0, 8)}</span>
              </>
            ) : (
              'Cuộc trò chuyện mới'
            )}
          </p>
        </div>
        <Button variant="secondary" size="sm" icon={<IconPlus size={16} />} onClick={chat.reset} disabled={isEmpty}>
          {/* Icon only on narrow screens; the name stays available to screen readers. */}
          <span className="sr-only sm:not-sr-only">Cuộc trò chuyện mới</span>
        </Button>
      </div>

      <div ref={threadRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="mx-auto w-full max-w-3xl space-y-6">
          {aiReady === false && <AiUnavailableNotice onRecheck={health.reload} />}

          {isEmpty ? (
            <EmptyState
              icon={<IconChat />}
              title="Bắt đầu trò chuyện"
              description="Hỏi trợ lý bằng tiếng Việt. Trợ lý nhớ ngữ cảnh trong cùng cuộc trò chuyện."
            >
              <p className="flex gap-2.5 rounded-card bg-accent-soft px-4 py-3 text-left text-sm text-accent-soft-fg">
                <IconInfo size={18} className="mt-0.5 shrink-0" />
                <span>
                Ở phiên bản hiện tại, trợ lý chỉ trò chuyện. Trợ lý chưa đọc hoặc thay đổi dữ liệu tài chính, du lịch
                hay ẩm thực của bạn.
                </span>
              </p>
            </EmptyState>
          ) : (
            <ol aria-label="Nội dung cuộc trò chuyện" aria-live="polite" className="space-y-6">
              {chat.messages.map((message) => (
                <ChatMessageItem
                  key={message.id}
                  message={message}
                  onRetry={chat.retry}
                  retryDisabled={chat.isSending}
                />
              ))}
              {chat.isSending && <TypingIndicator />}
            </ol>
          )}
        </div>
      </div>

      <div className="border-t border-border bg-chrome/90 backdrop-blur">
        <div className="mx-auto w-full max-w-3xl">
          <ChatComposer onSend={chat.send} isSending={chat.isSending} />
        </div>
      </div>
    </div>
  )
}
