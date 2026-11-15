import { Button } from '@/components/ui/Button'
import { InlineAlert } from '@/components/ui/InlineAlert'
import { StickyNote } from '@/components/ui/StickyNote'

import { useFinanceMonth } from '../hooks/useFinanceMonth'
import { BudgetPanel } from './BudgetPanel'
import { MonthSummary } from './MonthSummary'
import { SpendingByCategory } from './SpendingByCategory'
import { TransactionForm } from './TransactionForm'
import { TransactionList } from './TransactionList'

function LoadingMonth() {
  return (
    <div role="status" aria-label="Đang tải số liệu tháng" className="space-y-6">
      <div className="h-24 animate-pulse rounded-note bg-surface-2" />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="h-72 animate-pulse rounded-card bg-surface-2" />
        <div className="h-72 animate-pulse rounded-card bg-surface-2" />
      </div>
    </div>
  )
}

/** One month of finance. Keyed by month in the page, so switching month starts fresh. */
export function FinanceMonth({ month }: { month: string }) {
  const finance = useFinanceMonth(month)
  const { data } = finance

  if (data.status === 'loading') return <LoadingMonth />
  if (data.status === 'error') {
    return (
      <InlineAlert
        title="Không tải được số liệu tài chính"
        requestId={data.error.requestId}
        action={
          <Button variant="secondary" size="sm" onClick={data.reload}>
            Thử lại
          </Button>
        }
      >
        {data.error.message}
      </InlineAlert>
    )
  }

  const { report, transactions, categories } = data.data

  return (
    <div className="space-y-8">
      <MonthSummary report={report} />

      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <section aria-labelledby="transactions-heading" className="space-y-4">
          <h2 id="transactions-heading" className="text-lg font-extrabold text-fg">
            Giao dịch <span className="font-medium text-fg-subtle">({report.transaction_count})</span>
          </h2>
          <TransactionList
            transactions={transactions}
            saving={finance.saving}
            onDelete={(id) => void finance.removeTransaction(id)}
          />
        </section>

        {/* Adding is the frequent task: on narrow screens the form comes before the list. */}
        <div className="order-first space-y-8 lg:order-none">
          <StickyNote color="paper" tape="center" className="border border-border p-5">
            <TransactionForm categories={categories} onSubmit={finance.addTransaction} saving={finance.saving} />
          </StickyNote>
          <BudgetPanel
            month={month}
            budgets={report.budgets}
            categories={categories}
            saving={finance.saving}
            onAdd={finance.addBudget}
            onDelete={finance.removeBudget}
          />
          <SpendingByCategory items={report.expense_by_category} total={report.expense_total} />
        </div>
      </div>
    </div>
  )
}
