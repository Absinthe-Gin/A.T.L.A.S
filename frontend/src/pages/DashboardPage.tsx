import { useState } from 'react'
import { Link } from 'react-router'

import { IconArrowRight, IconChat } from '@/components/icons'
import { PageContainer } from '@/components/PageHeader'
import { buttonClasses } from '@/components/ui/buttonClasses'
import { StickyNote } from '@/components/ui/StickyNote'
import { ModuleNotes } from '@/features/modules/components/ModuleNotes'
import { SystemStatusPanel } from '@/features/system-status/components/SystemStatusPanel'
import { useSystemStatus } from '@/features/system-status/context'
import { summarize } from '@/features/system-status/status'
import { cn } from '@/utils/cn'
import { greeting } from '@/utils/greeting'

const SUMMARY_DOT = {
  neutral: 'bg-fg-subtle',
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
  primary: 'bg-primary',
  accent: 'bg-accent',
} as const

function Hero() {
  const summary = summarize(useSystemStatus())
  // Computed once per visit; the greeting does not need to change while the page is open.
  const [title] = useState(() => greeting(new Date()))

  return (
    <div className="max-w-xl">
      <p className="inline-flex items-center gap-2 rounded-full border border-border-strong bg-surface px-3 py-1 text-sm font-medium text-fg-muted shadow-raise">
        <span aria-hidden="true" className={cn('size-2 rounded-full', SUMMARY_DOT[summary.tone])} />
        {summary.label}
      </p>
      <h1 className="mt-5 text-5xl font-extrabold tracking-tight text-fg sm:text-6xl">
        <span className="marker">{title}</span>
      </h1>
      <p className="mt-5 max-w-[52ch] text-lg text-fg-muted text-pretty">
        Sổ tay cá nhân của bạn. Hỏi Atlas bằng tiếng Việt; tài chính, chuyến đi và những điều bạn muốn ghi nhớ sẽ
        lần lượt có mặt ở đây.
      </p>
      <div className="mt-7 flex flex-wrap gap-3">
        <Link to="/chat" className={buttonClasses('primary', 'md')}>
          <IconChat size={18} />
          Trò chuyện với Atlas
          <IconArrowRight size={16} />
        </Link>
        <a href="#modules-heading" className={buttonClasses('secondary', 'md')}>
          Xem các phân hệ
        </a>
      </div>
    </div>
  )
}

export function DashboardPage() {
  return (
    <PageContainer>
      <div className="grid items-start gap-x-12 gap-y-12 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <Hero />
        {/* The system status, pinned to the page like a card taped into a notebook. */}
        <StickyNote color="paper" tilt={0.5} tape="corners" className="border border-border lg:mt-6">
          <div className="p-5">
            <SystemStatusPanel />
          </div>
        </StickyNote>
      </div>

      <section aria-labelledby="modules-heading" className="scroll-mt-8 space-y-6 pt-4">
        <div>
          <h2 id="modules-heading" className="text-3xl font-extrabold tracking-tight text-fg">
            Các phân hệ
          </h2>
          <p className="mt-2 text-base text-fg-muted">
            Mỗi phân hệ có một màu riêng. Trợ lý AI đã dùng được; các phân hệ khác đang được xây dựng.
          </p>
        </div>
        <ModuleNotes />
      </section>
    </PageContainer>
  )
}
