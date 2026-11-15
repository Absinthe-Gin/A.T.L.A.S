import { ChatPanel } from '@/features/chat/components/ChatPanel'

export function ChatPage() {
  return (
    // Fill the viewport below the mobile top bar (57px), or the full height on desktop.
    <div className="h-[calc(100dvh-57px)] lg:h-dvh">
      <ChatPanel />
    </div>
  )
}
