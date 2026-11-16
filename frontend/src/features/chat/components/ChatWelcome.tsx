import type { ReactNode } from 'react'

import { IconCloud, IconPlane, IconUtensils, IconWallet } from '@/components/icons'

interface Suggestion {
  icon: ReactNode
  title: string
  prompt: string
}

/** Things the assistant can really do today, each backed by a module's tools. */
const SUGGESTIONS: Suggestion[] = [
  { icon: <IconWallet size={18} />, title: 'Ghi một khoản chi', prompt: 'Ghi giúp mình khoản chi 50k ăn trưa hôm nay' },
  { icon: <IconWallet size={18} />, title: 'Xem chi tiêu tháng này', prompt: 'Tháng này mình đã chi bao nhiêu tiền?' },
  { icon: <IconCloud size={18} />, title: 'Hỏi thời tiết', prompt: 'Thời tiết Đà Lạt mấy ngày tới thế nào?' },
  { icon: <IconUtensils size={18} />, title: 'Tìm món ngon', prompt: 'Món đặc sản ở Huế là gì?' },
  { icon: <IconPlane size={18} />, title: 'Tìm cách đi', prompt: 'Đi từ Hà Nội vào Đà Nẵng ngày 20/12 bằng gì?' },
]

interface ChatWelcomeProps {
  onPick: (prompt: string) => void
  disabled: boolean
  children: ReactNode
}

/** The start of a new conversation: a question, the composer, and things to try. */
export function ChatWelcome({ onPick, disabled, children }: ChatWelcomeProps) {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-6 px-4 py-10">
      <div className="text-center">
        <h2 className="text-3xl font-extrabold tracking-tight text-fg text-balance sm:text-4xl">
          Hôm nay Atlas giúp gì cho bạn?
        </h2>
        <p className="mt-2 text-fg-muted text-pretty">
          Hỏi bằng tiếng Việt. Atlas tra cứu tài chính, chuyến đi, thời tiết và quán ăn cho bạn.
        </p>
      </div>

      {children}

      <ul aria-label="Gợi ý" className="grid gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((suggestion) => (
          <li key={suggestion.title}>
            <button
              type="button"
              disabled={disabled}
              onClick={() => onPick(suggestion.prompt)}
              className="flex h-full w-full cursor-pointer items-start gap-3 rounded-card border border-border bg-surface px-4 py-3 text-left transition-[border-color,background-color] duration-150 hover:border-primary/40 hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-ring disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span className="mt-0.5 shrink-0 text-primary">{suggestion.icon}</span>
              <span className="min-w-0">
                <span className="block text-sm font-bold text-fg">{suggestion.title}</span>
                <span className="block text-sm text-fg-muted">{suggestion.prompt}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
