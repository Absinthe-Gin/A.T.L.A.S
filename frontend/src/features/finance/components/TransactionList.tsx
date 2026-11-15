import { useState } from 'react'

import { IconClose } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { IconButton } from '@/components/ui/IconButton'
import { cn } from '@/utils/cn'
import { formatDay, formatVnd } from '@/utils/money'

import type { Transaction } from '../types'

const KIND_LABEL = { income: 'Thu', expense: 'Chi', adjustment: 'Điều chỉnh' } as const

function signedAmount(transaction: Transaction): { text: string; className: string } {
  if (transaction.kind === 'income') {
    return { text: `+${formatVnd(transaction.amount)}`, className: 'text-success' }
  }
  if (transaction.kind === 'expense') {
    return { text: `−${formatVnd(transaction.amount)}`, className: 'text-fg' }
  }
  const prefix = transaction.amount > 0 ? '+' : ''
  return { text: `${prefix}${formatVnd(transaction.amount)}`, className: 'text-accent' }
}

function groupByDay(transactions: Transaction[]): [string, Transaction[]][] {
  const groups = new Map<string, Transaction[]>()
  for (const transaction of transactions) {
    const day = groups.get(transaction.occurred_on) ?? []
    day.push(transaction)
    groups.set(transaction.occurred_on, day)
  }
  return [...groups.entries()]
}

interface RowProps {
  transaction: Transaction
  onDelete: (id: string) => void
  disabled: boolean
}

function TransactionRow({ transaction, onDelete, disabled }: RowProps) {
  const [confirming, setConfirming] = useState(false)
  const amount = signedAmount(transaction)
  const title = transaction.note ?? transaction.category_name ?? KIND_LABEL[transaction.kind]

  return (
    <li className="flex animate-settle items-center gap-3 py-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-[0.9375rem] font-semibold text-fg">{title}</p>
        <p className="truncate text-xs text-fg-subtle">
          {KIND_LABEL[transaction.kind]}
          {transaction.category_name && transaction.note ? `, ${transaction.category_name}` : ''}
        </p>
      </div>
      <p className={cn('shrink-0 text-[0.9375rem] font-bold', amount.className)}>{amount.text}</p>
      {confirming ? (
        <div className="flex shrink-0 items-center gap-1">
          <Button variant="danger" size="sm" disabled={disabled} onClick={() => onDelete(transaction.id)}>
            Xóa
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setConfirming(false)}>
            Giữ lại
          </Button>
        </div>
      ) : (
        <IconButton
          label={`Xóa giao dịch ${title}`}
          icon={<IconClose size={16} />}
          disabled={disabled}
          onClick={() => setConfirming(true)}
        />
      )}
    </li>
  )
}

interface TransactionListProps {
  transactions: Transaction[]
  onDelete: (id: string) => void
  saving: boolean
}

export function TransactionList({ transactions, onDelete, saving }: TransactionListProps) {
  if (transactions.length === 0) {
    return (
      <p className="rounded-card border border-dashed border-border-strong px-4 py-8 text-center text-sm text-fg-muted">
        Tháng này chưa có giao dịch. Ghi khoản đầu tiên ở khung bên cạnh, hoặc nhắn cho Atlas.
      </p>
    )
  }

  return (
    <div className="space-y-5">
      {groupByDay(transactions).map(([day, items]) => (
        <section key={day} aria-label={formatDay(day)}>
          <h3 className="border-b border-border pb-1.5 text-sm font-bold text-fg-muted">{formatDay(day)}</h3>
          <ul className="divide-y divide-border">
            {items.map((transaction) => (
              <TransactionRow key={transaction.id} transaction={transaction} onDelete={onDelete} disabled={saving} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
