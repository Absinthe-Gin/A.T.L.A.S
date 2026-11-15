import { useCallback, useState } from 'react'

import { type AsyncData, useAsyncData } from '@/hooks/useAsyncData'
import { type ApiError, toApiError } from '@/services/api/errors'

import {
  createBudget,
  createCategory,
  createTransaction,
  deleteBudget,
  deleteTransaction,
  getMonthlyReport,
  listCategories,
  listTransactions,
} from '../api'
import type { BudgetCreate, Category, CategoryKind, MonthlyReport, Transaction, TransactionCreate } from '../types'

export interface FinanceMonthData {
  report: MonthlyReport
  transactions: Transaction[]
  categories: Category[]
}

/** Outcome of a change: either done, or the error to show next to the form that caused it. */
export type MutationResult = { ok: true } | { ok: false; error: ApiError }

export interface UseFinanceMonth {
  data: AsyncData<FinanceMonthData>
  addTransaction: (data: TransactionCreate) => Promise<MutationResult>
  removeTransaction: (id: string) => Promise<MutationResult>
  addBudget: (data: BudgetCreate) => Promise<MutationResult>
  removeBudget: (id: string) => Promise<MutationResult>
  addCategory: (name: string, kind: CategoryKind) => Promise<MutationResult>
  /** True while any change is being saved. */
  saving: boolean
}

/**
 * Everything the finance screen shows for one month. Totals always come from
 * the backend report; after a change the month is fetched again in the background.
 */
export function useFinanceMonth(month: string): UseFinanceMonth {
  const fetcher = useCallback(
    async (signal: AbortSignal): Promise<FinanceMonthData> => {
      const [report, page, categories] = await Promise.all([
        getMonthlyReport(month, signal),
        listTransactions(month, {}, signal),
        listCategories(undefined, signal),
      ])
      return { report, transactions: page.items, categories }
    },
    [month],
  )
  const data = useAsyncData(fetcher)
  const [saving, setSaving] = useState(false)
  const { refresh } = data

  const run = useCallback(
    async (change: () => Promise<unknown>): Promise<MutationResult> => {
      setSaving(true)
      try {
        await change()
        refresh()
        return { ok: true }
      } catch (error) {
        return { ok: false, error: toApiError(error) }
      } finally {
        setSaving(false)
      }
    },
    [refresh],
  )

  return {
    data,
    saving,
    addTransaction: (input) => run(() => createTransaction(input)),
    removeTransaction: (id) => run(() => deleteTransaction(id)),
    addBudget: (input) => run(() => createBudget(input)),
    removeBudget: (id) => run(() => deleteBudget(id)),
    addCategory: (name, kind) => run(() => createCategory(name, kind)),
  }
}
