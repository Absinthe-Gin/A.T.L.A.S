import { type FormEvent, type KeyboardEvent, useLayoutEffect, useRef, useState } from 'react'

import { IconSend } from '@/components/icons'
import { Spinner } from '@/components/ui/Spinner'
import { cn } from '@/utils/cn'

import { MESSAGE_MAX_LENGTH } from '../types'

const MAX_HEIGHT_PX = 200
// Show the character counter only when it starts to matter.
const COUNTER_THRESHOLD = MESSAGE_MAX_LENGTH - 500

interface ChatComposerProps {
  onSend: (text: string) => void
  isSending: boolean
}

export function ChatComposer({ onSend, isSending }: ChatComposerProps) {
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
    <form onSubmit={handleSubmit} className="px-4 py-3 sm:px-6">
      <div
        className={cn(
          'flex items-end gap-2 rounded-card border border-border-strong bg-surface p-2 shadow-raise',
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
          placeholder="Nhập tin nhắn…"
          aria-describedby="chat-input-hint"
          className="max-h-[200px] min-h-10 flex-1 resize-none bg-transparent px-2 py-2 text-[0.9375rem] text-fg outline-none placeholder:text-fg-subtle focus-visible:outline-none"
        />
        <button
          type="submit"
          disabled={!canSend}
          aria-label={isSending ? 'Đang gửi' : 'Gửi tin nhắn'}
          title="Gửi (Enter)"
          className={cn(
            'inline-flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-control',
            'transition-[background-color,color,box-shadow,translate] duration-150 ease-out active:translate-y-px',
            'btn-action text-action-fg',
            // Unavailable until there is something to send: neutral, not a faded action colour.
            'disabled:cursor-not-allowed disabled:translate-y-0 disabled:bg-surface-2 disabled:text-fg-subtle disabled:shadow-none',
          )}
        >
          {isSending ? <Spinner size={18} /> : <IconSend size={18} />}
        </button>
      </div>
      <div id="chat-input-hint" className="mt-1.5 flex justify-between gap-4 px-1 text-xs text-fg-subtle">
        {/* Keyboard hint; not useful with a touch keyboard. */}
        <span className="hidden sm:inline">
          <kbd className="font-sans font-medium">Enter</kbd> để gửi, <kbd className="font-sans font-medium">Shift + Enter</kbd> để xuống dòng
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
