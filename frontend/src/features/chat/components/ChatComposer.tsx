import { type FormEvent, type KeyboardEvent, useLayoutEffect, useRef, useState } from 'react'

import { IconSend, IconStop } from '@/components/icons'
import { cn } from '@/utils/cn'

import { MESSAGE_MAX_LENGTH } from '../types'

const MAX_HEIGHT_PX = 200
// Show the character counter only when it starts to matter.
const COUNTER_THRESHOLD = MESSAGE_MAX_LENGTH - 500

interface ChatComposerProps {
  onSend: (text: string) => void
  /** Stop waiting for the current reply. */
  onStop: () => void
  isSending: boolean
  autoFocus?: boolean
  placeholder?: string
}

export function ChatComposer({
  onSend,
  onStop,
  isSending,
  autoFocus = false,
  placeholder = 'Nhắn cho Atlas…',
}: ChatComposerProps) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const canSend = text.trim().length > 0 && !isSending

  // Grow with the content up to a limit, then scroll.
  useLayoutEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_HEIGHT_PX)}px`
  }, [text])

  const submit = () => {
    if (!canSend) return
    onSend(text)
    setText('')
    textareaRef.current?.focus()
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    submit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== 'Enter' || event.shiftKey || event.ctrlKey || event.metaKey || event.altKey) {
      return
    }
    event.preventDefault()
    // Enter also confirms a word in Vietnamese and other IME input; never send then.
    if (event.nativeEvent.isComposing || event.keyCode === 229) return
    if (!event.repeat) submit()
  }

  return (
    <form onSubmit={handleSubmit}>
      <div
        className={cn(
          'flex items-end gap-2 rounded-[1.375rem] border border-border-strong bg-surface p-2 pl-3 shadow-raise',
          'transition-[border-color,box-shadow] duration-150 ease-out',
          'focus-within:border-primary/60 focus-within:shadow-[0_0_0_3px_var(--primary-soft)]',
        )}
      >
        <label htmlFor="chat-input" className="sr-only">
          Tin nhắn
        </label>
        <textarea
          id="chat-input"
          ref={textareaRef}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          maxLength={MESSAGE_MAX_LENGTH}
          placeholder={placeholder}
          // Focus belongs in the composer when a chat opens; the user came here to type.
          autoFocus={autoFocus}
          aria-describedby="chat-input-hint"
          className="max-h-50 min-h-11 flex-1 resize-none bg-transparent px-1 py-2.5 text-[0.9375rem] text-fg outline-none placeholder:text-fg-subtle focus-visible:outline-none"
        />
        {isSending ? (
          <button
            type="button"
            onClick={onStop}
            aria-label="Dừng chờ câu trả lời"
            title="Dừng"
            className="inline-flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full border border-border-strong bg-surface text-fg transition-colors duration-150 hover:bg-surface-2"
          >
            <IconStop size={18} />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!canSend}
            aria-label="Gửi tin nhắn"
            title="Gửi (Enter)"
            className={cn(
              'inline-flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full',
              'transition-[background-color,color,box-shadow,translate] duration-150 ease-out active:translate-y-px',
              'btn-action text-action-fg',
              // Unavailable until there is something to send: neutral, not a faded action colour.
              'disabled:cursor-not-allowed disabled:translate-y-0 disabled:bg-surface-2 disabled:text-fg-subtle disabled:shadow-none',
            )}
          >
            <IconSend size={18} />
          </button>
        )}
      </div>
      <div id="chat-input-hint" className="mt-1.5 flex justify-between gap-4 px-2 text-xs text-fg-subtle">
        <span>
          {/* Keyboard hint; not useful with a touch keyboard. */}
          <span className="hidden sm:inline">
            <kbd className="font-sans font-medium">Enter</kbd> để gửi, <kbd className="font-sans font-medium">Shift + Enter</kbd> để xuống dòng.{' '}
          </span>
          Atlas có thể nhầm; hãy kiểm tra thông tin quan trọng.
        </span>
        {text.length >= COUNTER_THRESHOLD && (
          <span className={cn('ml-auto font-mono', text.length >= MESSAGE_MAX_LENGTH && 'text-danger')}>
            {text.length}/{MESSAGE_MAX_LENGTH}
          </span>
        )}
      </div>
    </form>
  )
}
