import { StickyNote } from '@/components/ui/StickyNote'
import { cn } from '@/utils/cn'
import { formatVnd } from '@/utils/money'

import type { MonthlyReport } from '../types'

interface FigureProps {
  label: string
  amount: number
  tone?: 'default' | 'income' | 'expense'
  signed?: boolean
}

function Figure({ label, amount, tone = 'default', signed = false }: FigureProps) {
  const text = signed && amount > 0 ? `+${formatVnd(amount)}` : formatVnd(amount)
  return (
    <div className="min-w-0">
      <dt className="text-sm font-medium text-fg-muted">{label}</dt>
      <dd
        className={cn(
          'mt-1 truncate text-xl font-extrabold tracking-tight sm:text-2xl',
          tone === 'income' && 'text-success',
          tone === 'expense' && 'text-danger',
          tone === 'default' && 'text-fg',
        )}
      >
        {text}
      </dd>
    </div>
  )
}

/** The month at a glance. Every number is computed by the backend. */
export function MonthSummary({ report }: { report: MonthlyReport }) {
  return (
    <StickyNote color="green" tape="none" className="px-5 py-4">
      <dl className="grid grid-cols-2 gap-x-6 gap-y-4 lg:grid-cols-4">
        <Figure label="Thu" amount={report.income_total} tone="income" />
        <Figure label="Chi" amount={report.expense_total} tone="expense" />
        <Figure label="Điều chỉnh" amount={report.adjustment_total} signed />
        <Figure label="Còn lại trong tháng" amount={report.net} signed />
      </dl>
    </StickyNote>
  )
}
