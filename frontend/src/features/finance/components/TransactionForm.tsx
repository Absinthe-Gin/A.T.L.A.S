import { type FormEvent, useId, useState } from 'react'

import { Button } from '@/components/ui/Button'
import { errorClasses, fieldClasses, hintClasses, labelClasses } from '@/components/ui/fieldClasses'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'
import { cn } from '@/utils/cn'
import { formatVnd, parseAmount, toIsoDate } from '@/utils/money'

import type { MutationResult } from '../hooks/useFinanceMonth'
import type { Category, TransactionCreate, TransactionKind } from '../types'

const KINDS: { value: TransactionKind; label: string }[] = [
  { value: 'expense', label: 'Chi' },
  { value: 'income', label: 'Thu' },
  { value: 'adjustment', label: 'Điều chỉnh' },
]

interface TransactionFormProps {
  categories: Category[]
  onSubmit: (data: TransactionCreate) => Promise<MutationResult>
  saving: boolean
}

export function TransactionForm({ categories, onSubmit, saving }: TransactionFormProps) {
  const id = useId()
  const [kind, setKind] = useState<TransactionKind>('expense')
  const [amountText, setAmountText] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [occurredOn, setOccurredOn] = useState(() => toIsoDate(new Date()))
  const [note, setNote] = useState('')
  const [touched, setTouched] = useState(false)
  const [serverError, setServerError] = useState<ApiError | null>(null)

  const amount = parseAmount(amountText)
  const amountError =
    amount === null
      ? 'Nhập số tiền, ví dụ 50000, 50.000, 50k hoặc 1,5tr.'
      : kind === 'adjustment'
        ? amount === 0
          ? 'Số tiền điều chỉnh phải khác 0.'
          : null
        : amount <= 0
          ? 'Số tiền phải lớn hơn 0.'
          : null
  const showAmountError = touched && amountError !== null
  const kindCategories = kind === 'adjustment' ? [] : categories.filter((category) => category.kind === kind)

  const changeKind = (next: TransactionKind) => {
    setKind(next)
    setCategoryId('')
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    if (amountError !== null || amount === null) return
    setServerError(null)
    const result = await onSubmit({
      kind,
      amount,
      category_id: categoryId || null,
      occurred_on: occurredOn,
      note: note.trim() || null,
    })
    if (result.ok) {
      setAmountText('')
      setNote('')
      setTouched(false)
    } else {
      setServerError(result.error)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`} className="text-lg font-extrabold text-fg">
        Ghi giao dịch
      </h2>

      <fieldset>
        <legend className="sr-only">Loại giao dịch</legend>
        <div className="grid grid-cols-3 gap-1 rounded-control bg-surface-2 p-1">
          {KINDS.map((option) => (
            <label
              key={option.value}
              className={cn(
                'flex min-h-10 cursor-pointer items-center justify-center rounded-[0.5rem] text-sm font-semibold transition-colors duration-150',
                'has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-ring',
                kind === option.value ? 'bg-surface text-fg shadow-raise' : 'text-fg-muted hover:text-fg',
              )}
            >
              <input
                type="radio"
                name={`${id}-kind`}
                value={option.value}
                checked={kind === option.value}
                onChange={() => changeKind(option.value)}
                className="sr-only"
              />
              {option.label}
            </label>
          ))}
        </div>
      </fieldset>

      <div>
        <label htmlFor={`${id}-amount`} className={labelClasses}>
          Số tiền
        </label>
        <input
          id={`${id}-amount`}
          inputMode={kind === 'adjustment' ? 'text' : 'numeric'}
          autoComplete="off"
          value={amountText}
          onChange={(event) => setAmountText(event.target.value)}
          onBlur={() => setTouched(true)}
          placeholder={kind === 'adjustment' ? 'Ví dụ: -20k hoặc 50000' : 'Ví dụ: 45k'}
          aria-invalid={showAmountError}
          aria-describedby={`${id}-amount-help`}
          className={fieldClasses(showAmountError)}
        />
        <p id={`${id}-amount-help`} className={showAmountError ? errorClasses : hintClasses} aria-live="polite">
          {showAmountError ? amountError : amount !== null && amount !== 0 ? `= ${formatVnd(amount)}` : 'Đơn vị: đồng'}
        </p>
      </div>

      {kind !== 'adjustment' && (
        <div>
          <label htmlFor={`${id}-category`} className={labelClasses}>
            Danh mục
          </label>
          <select
            id={`${id}-category`}
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
            className={fieldClasses()}
          >
            <option value="">Chưa phân loại</option>
            {kindCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="grid gap-4">
        <div>
          <label htmlFor={`${id}-date`} className={labelClasses}>
            Ngày
          </label>
          <input
            id={`${id}-date`}
            type="date"
            required
            value={occurredOn}
            onChange={(event) => setOccurredOn(event.target.value)}
            className={fieldClasses()}
          />
        </div>
        <div>
          <label htmlFor={`${id}-note`} className={labelClasses}>
            Ghi chú
          </label>
          <input
            id={`${id}-note`}
            maxLength={500}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Không bắt buộc"
            className={fieldClasses()}
          />
        </div>
      </div>

      {serverError && (
        <InlineAlert title="Chưa lưu được giao dịch" requestId={serverError.requestId}>
          {serverError.message}
        </InlineAlert>
      )}

      <Button type="submit" loading={saving} className="w-full">
        Lưu giao dịch
      </Button>
    </form>
  )
}
