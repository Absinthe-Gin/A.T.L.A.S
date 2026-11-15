import { IconGlobe } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'

import type { ChatMessage } from '../types'
import { PendingActionCard } from './PendingActionCard'

type UserChatMessage = Extract<ChatMessage, { role: 'user' }>
type AssistantChatMessage = Extract<ChatMessage, { role: 'assistant' }>

interface ChatMessageItemProps {
  message: ChatMessage
  onRetry: (messageId: string) => void
  onResolveAction: (id: string, decision: 'confirm' | 'cancel') => Promise<ApiError | null>
  retryDisabled: boolean
}

/** The user's words: in the action colour, aligned right. Grows out of its corner when sent. */
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
          'max-w-[85%] origin-bottom-right animate-pop whitespace-pre-wrap break-words rounded-bubble rounded-br-sm px-4 py-2.5 text-[0.9375rem] sm:max-w-[70%] ' +
          'transition-[background-color,color,border-color] duration-200 ' +
          (failed ? 'border border-danger bg-surface text-fg' : 'btn-action text-action-fg')
        }
      >
        {message.content}
      </div>
      {failed && message.error && (
        <InlineAlert
          className="w-full max-w-md"
          title="Chưa gửi được tin nhắn"
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

/** Name line shared by the assistant's replies and its typing indicator. */
function AssistantName() {
  return (
    <p className="mb-1.5 flex items-center gap-2 text-xs font-semibold text-accent">
      <span className="flex size-6 items-center justify-center rounded-full bg-accent-soft text-accent-soft-fg">
        <IconGlobe size={14} />
      </span>
      Atlas
    </p>
  )
}

/** The assistant's words: a white card on the notebook page, introduced by its name. */
function AssistantMessage({
  message,
  onResolveAction,
}: {
  message: AssistantChatMessage
  onResolveAction: ChatMessageItemProps['onResolveAction']
}) {
  const showDetails = message.intent !== 'general' || message.toolCalls.length > 0

  return (
    <li className="animate-rise">
      <AssistantName />
      <div className="ml-8 max-w-[85%] rounded-bubble rounded-tl-sm border border-border bg-surface px-4 py-3 shadow-raise sm:max-w-[75%]">
        <div className="whitespace-pre-wrap break-words text-[0.9375rem] text-fg">{message.content}</div>
      </div>
      {showDetails && (
        <dl aria-label="Chi tiết xử lý" className="mt-2 space-y-0.5 pl-8 text-xs text-fg-subtle">
          <div className="flex gap-1.5">
            <dt>Ý định:</dt>
            <dd className="font-mono">{message.intent}</dd>
          </div>
          {message.toolCalls.length > 0 && (
            <div className="flex gap-1.5">
              <dt className="shrink-0">Công cụ:</dt>
              <dd className="flex flex-wrap gap-x-3">
                {message.toolCalls.map((call, index) => (
                  // A tool can run more than once per reply; the position keeps keys unique.
                  <span key={`${call.name}-${index}`}>
                    <span className="font-mono">{call.name}</span>{' '}
                    <span className={call.status === 'success' ? 'text-success' : 'text-danger'}>
                      ({call.status === 'success' ? 'thành công' : 'thất bại'})
                    </span>
                  </span>
                ))}
              </dd>
            </div>
          )}
        </dl>
      )}
      {message.pendingActions.length > 0 && (
        <div className="mt-3 space-y-2">
          {message.pendingActions.map((action) => (
            <PendingActionCard key={action.id} action={action} onResolve={onResolveAction} />
          ))}
        </div>
      )}
    </li>
  )
}

export function ChatMessageItem({ message, onRetry, retryDisabled, onResolveAction }: ChatMessageItemProps) {
  return message.role === 'user' ? (
    <UserMessage message={message} onRetry={onRetry} retryDisabled={retryDisabled} />
  ) : (
    <AssistantMessage message={message} onResolveAction={onResolveAction} />
  )
}

export function TypingIndicator() {
  return (
    <li className="animate-settle" role="status">
      <AssistantName />
      <span className="sr-only">Trợ lý đang soạn câu trả lời</span>
      <span aria-hidden="true" className="flex h-6 items-center gap-1.5 pl-8">
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
