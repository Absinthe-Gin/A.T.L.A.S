import { useEffect, useState } from 'react'

import { IconCheck, IconCopy, IconGlobe, IconInfo } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { IconButton } from '@/components/ui/IconButton'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'
import { reportError } from '@/utils/reportError'

import { toolLabel } from '../tools'
import type { ChatMessage } from '../types'
import { MessageMarkdown } from './MessageMarkdown'
import { PendingActionCard } from './PendingActionCard'

type UserChatMessage = Extract<ChatMessage, { role: 'user' }>
type AssistantChatMessage = Extract<ChatMessage, { role: 'assistant' }>

interface ChatMessageItemProps {
  message: ChatMessage
  onRetry: (messageId: string) => void
  onResolveAction: (id: string, decision: 'confirm' | 'cancel') => Promise<ApiError | null>
  retryDisabled: boolean
}

/** The user's words, on the right, in a soft bubble. */
function UserMessage({
  message,
  onRetry,
  retryDisabled,
}: Pick<ChatMessageItemProps, 'onRetry' | 'retryDisabled'> & { message: UserChatMessage }) {
  const failed = message.status === 'failed'

  return (
    <li className="flex flex-col items-end gap-2">
      <p className="sr-only">Bạn:</p>
      <div
        className={
          'max-w-[85%] origin-bottom-right animate-pop whitespace-pre-wrap break-words rounded-bubble px-4 py-2.5 text-[0.9375rem] text-fg sm:max-w-[75%] ' +
          (failed ? 'border border-danger bg-surface' : 'bg-primary-soft')
        }
      >
        {message.content}
      </div>
      {failed && message.error && (
        <InlineAlert
          className="w-full max-w-md"
          title="Chưa có câu trả lời"
          requestId={message.error.requestId}
          action={
            <Button variant="secondary" size="sm" onClick={() => onRetry(message.id)} disabled={retryDisabled}>
              Gửi lại
            </Button>
          }
        >
          {message.error.message}
        </InlineAlert>
      )}
    </li>
  )
}

function AssistantAvatar() {
  return (
    <span
      aria-hidden="true"
      className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent-soft-fg"
    >
      <IconGlobe size={16} />
    </span>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const timer = window.setTimeout(() => setCopied(false), 2000)
    return () => window.clearTimeout(timer)
  }, [copied])

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
    } catch (error) {
      reportError(error, { context: 'copy chat reply' })
    }
  }

  return (
    <IconButton
      label={copied ? 'Đã sao chép' : 'Sao chép câu trả lời'}
      icon={copied ? <IconCheck size={16} className="text-success" /> : <IconCopy size={16} />}
      onClick={() => void copy()}
      className="size-9"
    />
  )
}

/** The assistant's words: plain text on the page, like a written answer, with its avatar. */
function AssistantMessage({
  message,
  onResolveAction,
}: {
  message: AssistantChatMessage
  onResolveAction: ChatMessageItemProps['onResolveAction']
}) {
  const sources = [...new Map(message.toolCalls.map((call) => [toolLabel(call.name), call])).entries()]

  return (
    <li className="flex animate-rise gap-3">
      <AssistantAvatar />
      <div className="min-w-0 flex-1">
        <p className="sr-only">Atlas:</p>
        <MessageMarkdown content={message.content} />

        {message.pendingActions.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.pendingActions.map((action) => (
              <PendingActionCard key={action.id} action={action} onResolve={onResolveAction} />
            ))}
          </div>
        )}

        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
          <CopyButton text={message.content} />
          {sources.length > 0 && (
            <ul aria-label="Dữ liệu đã dùng" className="flex flex-wrap gap-1.5 text-xs">
              {sources.map(([label, call]) => (
                <li
                  key={label}
                  title={call.name}
                  className={
                    'rounded-full px-2.5 py-1 font-medium ' +
                    (call.status === 'error' ? 'bg-danger-soft text-danger' : 'bg-surface-2 text-fg-muted')
                  }
                >
                  {call.status === 'error' ? `${label}: không lấy được` : `Đã dùng ${label}`}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </li>
  )
}

/** A short note from the system, e.g. that a proposal was confirmed. */
function SystemNote({ content }: { content: string }) {
  return (
    <li className="flex items-start justify-center gap-2 text-center text-xs text-fg-subtle">
      <IconInfo size={14} className="mt-0.5 shrink-0" />
      <span>{content}</span>
    </li>
  )
}

export function ChatMessageItem({ message, onRetry, retryDisabled, onResolveAction }: ChatMessageItemProps) {
  if (message.role === 'user') {
    return <UserMessage message={message} onRetry={onRetry} retryDisabled={retryDisabled} />
  }
  if (message.role === 'system') return <SystemNote content={message.content} />
  return <AssistantMessage message={message} onResolveAction={onResolveAction} />
}

export function TypingIndicator() {
  return (
    <li className="flex animate-settle gap-3" role="status">
      <AssistantAvatar />
      <span className="sr-only">Atlas đang soạn câu trả lời</span>
      <span aria-hidden="true" className="flex h-8 items-center gap-1.5">
        {[0, 140, 280].map((delay) => (
          <span
            key={delay}
            className="size-1.5 animate-typing rounded-full bg-accent"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </span>
    </li>
  )
}
