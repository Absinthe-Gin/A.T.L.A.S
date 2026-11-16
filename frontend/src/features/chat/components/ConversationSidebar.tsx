import { type FormEvent, useId, useMemo, useState } from 'react'
import { NavLink } from 'react-router'

import { IconPencil, IconPlus, IconSidebar, IconTrash } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { IconButton } from '@/components/ui/IconButton'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'
import { cn } from '@/utils/cn'

import { conversationTitle, groupConversations } from '../history'
import type { UseConversations } from '../hooks/useConversations'
import type { ConversationSummary } from '../types'

interface ConversationSidebarProps {
  conversations: UseConversations
  activeId: string | null
  onNewChat: () => void
  /** After a click on a conversation, e.g. to close the mobile drawer. */
  onNavigate?: () => void
  /** The open conversation was deleted. */
  onActiveDeleted: () => void
  /** Folded to a narrow strip of icons (desktop only). */
  collapsed?: boolean
  /** Shows the fold/unfold button. Omit where folding makes no sense, e.g. the mobile drawer. */
  onToggleCollapsed?: () => void
}

type Mode = { kind: 'view' } | { kind: 'rename' } | { kind: 'confirmDelete' }

function ConversationRow({
  item,
  active,
  onNavigate,
  onRename,
  onDelete,
}: {
  item: ConversationSummary
  active: boolean
  onNavigate?: () => void
  onRename: (title: string) => Promise<ApiError | null>
  onDelete: () => Promise<ApiError | null>
}) {
  const id = useId()
  const [mode, setMode] = useState<Mode>({ kind: 'view' })
  const [title, setTitle] = useState(conversationTitle(item))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const name = conversationTitle(item)

  const run = async (change: () => Promise<ApiError | null>) => {
    setBusy(true)
    const failure = await change()
    setBusy(false)
    setError(failure)
    if (!failure) setMode({ kind: 'view' })
  }

  const submitRename = (event: FormEvent) => {
    event.preventDefault()
    if (!title.trim()) return
    void run(() => onRename(title.trim()))
  }

  if (mode.kind === 'rename') {
    return (
      <li className="px-1 py-1">
        <form onSubmit={submitRename} className="space-y-1.5">
          <label htmlFor={`${id}-title`} className="sr-only">
            Tên mới cho {name}
          </label>
          <input
            id={`${id}-title`}
            value={title}
            maxLength={200}
            // The user just asked to rename: the field is where they type next.
            autoFocus
            onChange={(event) => setTitle(event.target.value)}
            onKeyDown={(event) => event.key === 'Escape' && setMode({ kind: 'view' })}
            className="min-h-10 w-full rounded-control border border-primary/60 bg-surface px-2.5 text-sm text-fg outline-none"
          />
          <div className="flex gap-1.5">
            <Button type="submit" size="sm" loading={busy} disabled={!title.trim()}>
              Lưu
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => setMode({ kind: 'view' })}>
              Hủy
            </Button>
          </div>
          {error && <p className="text-xs text-danger">{error.message}</p>}
        </form>
      </li>
    )
  }

  if (mode.kind === 'confirmDelete') {
    return (
      <li className="rounded-control bg-danger-soft px-2.5 py-2">
        <p className="text-sm text-fg">
          Xóa <span className="font-semibold">{name}</span>? Tin nhắn và đề xuất trong đó sẽ mất.
        </p>
        <div className="mt-2 flex gap-1.5">
          <Button variant="danger" size="sm" loading={busy} onClick={() => void run(onDelete)}>
            Xóa
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setMode({ kind: 'view' })}>
            Giữ lại
          </Button>
        </div>
        {error && <p className="mt-1 text-xs text-danger">{error.message}</p>}
      </li>
    )
  }

  return (
    <li className="group relative">
      <NavLink
        to={`/chat/${item.id}`}
        onClick={onNavigate}
        className={cn(
          'flex min-h-10 items-center rounded-control py-2 pr-20 pl-3 text-sm transition-colors duration-150',
          active ? 'bg-surface font-semibold text-fg shadow-raise' : 'text-fg-muted hover:bg-fg/5 hover:text-fg',
        )}
      >
        <span className="truncate">{name}</span>
      </NavLink>
      {/* Visible on hover, keyboard focus, and always for the open conversation. */}
      <div
        className={cn(
          'absolute top-1/2 right-1 flex -translate-y-1/2 gap-0.5 transition-opacity duration-150',
          active ? 'opacity-100' : 'opacity-0 group-hover:opacity-100 focus-within:opacity-100',
        )}
      >
        <IconButton
          label={`Đổi tên ${name}`}
          icon={<IconPencil size={15} />}
          className="size-8"
          onClick={() => {
            setTitle(name)
            setMode({ kind: 'rename' })
          }}
        />
        <IconButton
          label={`Xóa ${name}`}
          icon={<IconTrash size={15} />}
          className="size-8"
          onClick={() => setMode({ kind: 'confirmDelete' })}
        />
      </div>
    </li>
  )
}

/** Folded history: one centred letter per conversation, named for screen readers and tooltips. */
function FoldedHistory({
  items,
  activeId,
  onNewChat,
  onToggleCollapsed,
  onNavigate,
}: {
  items: ConversationSummary[]
  activeId: string | null
  onNewChat: () => void
  onToggleCollapsed: () => void
  onNavigate?: () => void
}) {
  return (
    <nav aria-label="Lịch sử trò chuyện" className="flex h-full min-h-0 flex-col items-center gap-3 py-3">
      <IconButton label="Cuộc trò chuyện mới" icon={<IconPlus size={18} />} onClick={onNewChat} />
      <IconButton label="Mở rộng lịch sử trò chuyện" icon={<IconSidebar size={18} />} onClick={onToggleCollapsed} />
      <ul className="min-h-0 flex-1 space-y-1.5 overflow-y-auto border-t border-border pt-3">
        {items.map((item) => {
          const name = conversationTitle(item)
          const active = item.id === activeId
          return (
            <li key={item.id}>
              <NavLink
                to={`/chat/${item.id}`}
                onClick={onNavigate}
                title={name}
                aria-label={name}
                className={cn(
                  'flex size-9 items-center justify-center rounded-full text-sm font-bold transition-colors duration-150',
                  active
                    ? 'bg-primary-soft text-primary-soft-fg shadow-raise'
                    : 'bg-surface-2 text-fg-muted hover:bg-fg/10 hover:text-fg',
                )}
              >
                {name.charAt(0).toLocaleUpperCase('vi-VN')}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

/** The conversation history, grouped by when each conversation was last active. */
export function ConversationSidebar({
  conversations,
  activeId,
  onNewChat,
  onNavigate,
  onActiveDeleted,
  collapsed = false,
  onToggleCollapsed,
}: ConversationSidebarProps) {
  const { data } = conversations
  // Grouping uses the time the list was loaded; it does not need to tick.
  const [now] = useState(() => new Date())
  const groups = useMemo(
    () => (data.status === 'success' ? groupConversations(data.data.items, now) : []),
    [data, now],
  )

  if (collapsed && onToggleCollapsed) {
    return (
      <FoldedHistory
        items={data.status === 'success' ? data.data.items : []}
        activeId={activeId}
        onNewChat={onNewChat}
        onToggleCollapsed={onToggleCollapsed}
        onNavigate={onNavigate}
      />
    )
  }

  return (
    <nav aria-label="Lịch sử trò chuyện" className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 p-3">
        <Button variant="secondary" icon={<IconPlus size={16} />} onClick={onNewChat} className="min-w-0 flex-1 justify-start">
          Cuộc trò chuyện mới
        </Button>
        {onToggleCollapsed && (
          <IconButton label="Thu gọn lịch sử trò chuyện" icon={<IconSidebar size={18} />} onClick={onToggleCollapsed} />
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-4">
        {data.status === 'loading' && (
          <div role="status" aria-label="Đang tải lịch sử" className="space-y-2 pt-2">
            {[0, 1, 2, 3].map((row) => (
              <div key={row} className="h-9 animate-pulse rounded-control bg-surface-2" />
            ))}
          </div>
        )}

        {data.status === 'error' && (
          <InlineAlert
            title="Không tải được lịch sử"
            requestId={data.error.requestId}
            action={
              <Button variant="secondary" size="sm" onClick={data.reload}>
                Thử lại
              </Button>
            }
          >
            {data.error.message}
          </InlineAlert>
        )}

        {data.status === 'success' && groups.length === 0 && (
          <p className="px-2 pt-2 text-sm text-fg-subtle">
            Chưa có cuộc trò chuyện nào. Những gì bạn hỏi Atlas sẽ được lưu ở đây.
          </p>
        )}

        {groups.map((group) => (
          <section key={group.label} aria-label={group.label} className="pt-3">
            <h3 className="px-3 pb-1 text-xs font-semibold text-fg-subtle">{group.label}</h3>
            <ul className="space-y-0.5">
              {group.items.map((item) => (
                <ConversationRow
                  key={item.id}
                  item={item}
                  active={item.id === activeId}
                  onNavigate={onNavigate}
                  onRename={(title) => conversations.rename(item.id, title)}
                  onDelete={async () => {
                    const error = await conversations.remove(item.id)
                    if (!error && item.id === activeId) onActiveDeleted()
                    return error
                  }}
                />
              ))}
            </ul>
          </section>
        ))}
      </div>
    </nav>
  )
}
