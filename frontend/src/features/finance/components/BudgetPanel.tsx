import { type FormEvent, useId, useState } from 'react'

import { IconClose } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { errorClasses, fieldClasses, labelClasses } from '@/components/ui/fieldClasses'
import { IconButton } from '@/components/ui/IconButton'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'
import { cn } from '@/utils/cn'
import { formatVnd, parseAmount } from '@/utils/money'

import type { MutationResult } from '../hooks/useFinanceMonth'
import type { Budget, BudgetCreate, Category } from '../types'

function BudgetRow({ budget, onDelete, disabled }: { budget: Budget; onDelete: () => void; disabled: boolean }) {
  const name = budget.category_name ?? 'Tổng chi tiêu'
  const width = Math.min(budget.used_percent, 100)
  const tone = budget.over_budget ? 'bg-danger' : budget.used_percent >= 80 ? 'bg-warning' : 'bg-success'

  return (
    <li className="py-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-[0.9375rem] font-semibold text-fg">{name}</p>
          <p className={cn('text-xs', budget.over_budget ? 'font-semibold text-danger' : 'text-fg-subtle')}>
            {budget.over_budget
              ? `Vượt ${formatVnd(-budget.remaining)}`
              : `Còn ${formatVnd(budget.remaining)} / ${formatVnd(budget.amount)}`}
          </p>
        </div>
        <IconButton label={`Xóa ngân sách ${name}`} icon={<IconClose size={16} />} disabled={disabled} onClick={onDelete} />
      </div>
      <div
        role="progressbar"
        aria-label={`Đã dùng ngân sách ${name}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={width}
        aria-valuetext={`${budget.used_percent}%`}
        className="mt-2 h-2 overflow-hidden rounded-full bg-surface-2"
      >
        <div className={cn('h-full rounded-full transition-[width] duration-300 ease-out', tone)} style={{ width: `${width}%` }} />
      </div>
    </li>
  )
}

interface BudgetPanelProps {
  month: string
  budgets: Budget[]
  categories: Category[]
  saving: boolean
  onAdd: (data: BudgetCreate) => Promise<MutationResult>
  onDelete: (id: string) => Promise<MutationResult>
}

export function BudgetPanel({ month, budgets, categories, saving, onAdd, onDelete }: BudgetPanelProps) {
  const id = useId()
  const [categoryId, setCategoryId] = useState('')
  const [amountText, setAmountText] = useState('')
  const [touched, setTouched] = useState(false)
  const [serverError, setServerError] = useState<ApiError | null>(null)

  const amount = parseAmount(amountText)
  const amountError = amount === null || amount <= 0 ? 'Nhập hạn mức lớn hơn 0, ví dụ 3tr.' : null
  const used = new Set(budgets.map((budget) => budget.category_id ?? ''))
  const options = categories.filter((category) => category.kind === 'expense' && !used.has(category.id))
  const overallTaken = used.has('')
  // Never point at a choice that is no longer offered (e.g. the overall budget already exists).
  const selected = categoryId && options.some((o) => o.id === categoryId) ? categoryId : overallTaken ? (options[0]?.id ?? '') : ''
  const nothingLeft = overallTaken && options.length === 0

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    if (amountError !== null || amount === null) return
    setServerError(null)
    if (nothingLeft) return
    const result = await onAdd({ month, category_id: selected || null, amount })
    if (result.ok) {
      setAmountText('')
      setTouched(false)
    } else {
      setServerError(result.error)
    }
  }

  return (
    <section aria-labelledby={`${id}-title`} className="space-y-3">
      <h2 id={`${id}-title`} className="text-lg font-extrabold text-fg">
        Ngân sách
      </h2>

      {budgets.length === 0 ? (
        <p className="text-sm text-fg-muted">Chưa đặt ngân sách cho tháng này.</p>
      ) : (
        <ul className="divide-y divide-border">
          {budgets.map((budget) => (
            <BudgetRow key={budget.id} budget={budget} disabled={saving} onDelete={() => void onDelete(budget.id)} />
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-3 border-t border-border pt-3">
        <div className="grid grid-cols-[1fr_8rem] gap-2">
          <div>
            <label htmlFor={`${id}-category`} className={labelClasses}>
              Áp dụng cho
            </label>
            <select
              id={`${id}-category`}
              value={selected}
              disabled={nothingLeft}
              onChange={(event) => setCategoryId(event.target.value)}
              className={fieldClasses()}
            >
              {!overallTaken && <option value="">Tổng chi tiêu</option>}
              {options.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor={`${id}-amount`} className={labelClasses}>
              Hạn mức
            </label>
            <input
              id={`${id}-amount`}
              inputMode="numeric"
              autoComplete="off"
              value={amountText}
              onChange={(event) => setAmountText(event.target.value)}
              placeholder="3tr"
              aria-invalid={touched && amountError !== null}
              aria-describedby={`${id}-amount-error`}
              className={fieldClasses(touched && amountError !== null)}
            />
          </div>
        </div>
        {touched && amountError && (
          <p id={`${id}-amount-error`} className={errorClasses}>
            {amountError}
          </p>
        )}
        {serverError && (
          <InlineAlert title="Chưa đặt được ngân sách" requestId={serverError.requestId}>
            {serverError.message}
          </InlineAlert>
        )}
        <Button type="submit" variant="secondary" loading={saving} disabled={nothingLeft} className="w-full">
          {nothingLeft ? 'Mọi danh mục đã có ngân sách' : 'Đặt ngân sách'}
        </Button>
      </form>
    </section>
  )
}
