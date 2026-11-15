/** Mirrors `backend/app/modules/finance/schemas.py`. Amounts are whole đồng. */

import type { Page } from '@/types/api'

export type CategoryKind = 'income' | 'expense'
export type TransactionKind = 'income' | 'expense' | 'adjustment'

export interface Category {
  id: string
  name: string
  kind: CategoryKind
}

export interface Transaction {
  id: string
  kind: TransactionKind
  amount: number
  currency: string
  category_id: string | null
  category_name: string | null
  occurred_on: string
  note: string | null
  created_at: string
}

export interface TransactionCreate {
  kind: TransactionKind
  amount: number
  category_id: string | null
  occurred_on: string
  note: string | null
}

export interface Budget {
  id: string
  month: string
  category_id: string | null
  category_name: string | null
  amount: number
  spent: number
  remaining: number
  used_percent: number
  over_budget: boolean
}

export interface BudgetCreate {
  month: string
  category_id: string | null
  amount: number
}

export interface CategoryTotal {
  category_id: string | null
  category_name: string
  total: number
}

export interface MonthlyReport {
  month: string
  currency: string
  income_total: number
  expense_total: number
  adjustment_total: number
  net: number
  transaction_count: number
  expense_by_category: CategoryTotal[]
  budgets: Budget[]
}

export type TransactionPage = Page<Transaction>
