import { formatVnd } from '@/utils/money'

import type { CategoryTotal } from '../types'

/** Spending per category as plain bars; the share is shown in words too. */
export function SpendingByCategory({ items, total }: { items: CategoryTotal[]; total: number }) {
  return (
    <section aria-labelledby="spending-heading" className="space-y-3">
      <h2 id="spending-heading" className="text-lg font-extrabold text-fg">
        Chi theo danh mục
      </h2>
      {items.length === 0 ? (
        <p className="text-sm text-fg-muted">Chưa có khoản chi nào.</p>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => {
            const share = total > 0 ? Math.round((item.total * 100) / total) : 0
            return (
              <li key={item.category_id ?? 'none'}>
                <div className="flex items-baseline justify-between gap-2 text-sm">
                  <span className="truncate font-semibold text-fg">{item.category_name}</span>
                  <span className="shrink-0 text-fg-muted">
                    {formatVnd(item.total)} <span className="text-fg-subtle">({share}%)</span>
                  </span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-2" aria-hidden="true">
                  <div className="h-full rounded-full bg-note-green-ink" style={{ width: `${share}%` }} />
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
