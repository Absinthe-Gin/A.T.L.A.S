import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { IconClose, IconSidebar } from '@/components/icons'
import { IconButton } from '@/components/ui/IconButton'
import { ChatPanel } from '@/features/chat/components/ChatPanel'
import { ConversationSidebar } from '@/features/chat/components/ConversationSidebar'
import { useConversations } from '@/features/chat/hooks/useConversations'
import { HISTORY_STORAGE_KEY, useSidebarCollapsed } from '@/hooks/useSidebarCollapsed'
import { cn } from '@/utils/cn'

export function ChatPage() {
  const { conversationId = null } = useParams()
  const navigate = useNavigate()
  const conversations = useConversations()
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyCollapsed, toggleHistoryCollapsed] = useSidebarCollapsed(HISTORY_STORAGE_KEY)
  const { data } = conversations
  const title =
    data.status === 'success' ? (data.data.items.find((item) => item.id === conversationId)?.title ?? null) : null

  // The mobile history drawer closes with Escape, like any dialog.
  useEffect(() => {
    if (!historyOpen) return
    const onKey = (event: KeyboardEvent) => event.key === 'Escape' && setHistoryOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [historyOpen])

  const goToNewChat = () => {
    setHistoryOpen(false)
    navigate('/chat')
  }

  // The desktop column can fold to icons; the mobile drawer is always the full list.
  const desktopSidebar = (
    <ConversationSidebar
      conversations={conversations}
      activeId={conversationId}
      onNewChat={goToNewChat}
      onActiveDeleted={() => navigate('/chat', { replace: true })}
      collapsed={historyCollapsed}
      onToggleCollapsed={toggleHistoryCollapsed}
    />
  )

  const drawerSidebar = (
    <ConversationSidebar
      conversations={conversations}
      activeId={conversationId}
      onNewChat={goToNewChat}
      onNavigate={() => setHistoryOpen(false)}
      onActiveDeleted={() => navigate('/chat', { replace: true })}
    />
  )

  return (
    // Fill the viewport below the mobile top bar (57px), or the full height on desktop.
    <div className="flex h-[calc(100dvh-57px)] lg:h-dvh">
      <aside
        className={cn(
          'hidden shrink-0 border-r border-border bg-chrome/60 transition-[width] duration-250 ease-out lg:block',
          historyCollapsed ? 'w-[4.5rem]' : 'w-72',
        )}
      >
        {desktopSidebar}
      </aside>

      {historyOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Đóng lịch sử trò chuyện"
            onClick={() => setHistoryOpen(false)}
            className="absolute inset-0 animate-settle bg-fg/30"
          />
          <aside className="absolute inset-y-0 left-0 flex w-[min(20rem,85vw)] animate-rise flex-col border-r border-border bg-bg shadow-lift">
            <div className="flex items-center justify-between border-b border-border px-3 py-2">
              <p className="text-sm font-bold text-fg">Lịch sử trò chuyện</p>
              <IconButton label="Đóng lịch sử trò chuyện" icon={<IconClose size={18} />} onClick={() => setHistoryOpen(false)} />
            </div>
            <div className="min-h-0 flex-1">{drawerSidebar}</div>
          </aside>
        </div>
      )}

      <div className="min-w-0 flex-1">
        <ChatPanel
          conversationId={conversationId}
          title={title}
          onConversationCreated={(id) => navigate(`/chat/${id}`, { replace: true })}
          onReply={data.refresh}
          onNewChat={goToNewChat}
          headerStart={
            <IconButton
              label="Mở lịch sử trò chuyện"
              icon={<IconSidebar size={18} />}
              onClick={() => setHistoryOpen(true)}
              className="lg:hidden"
            />
          }
        />
      </div>
    </div>
  )
}
