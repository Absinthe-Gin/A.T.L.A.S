import { apiClient } from '@/services/api/client'

import type {
  Budget,
  BudgetCreate,
  Category,
  CategoryKind,
  MonthlyReport,
  Transaction,
  TransactionCreate,
  TransactionPage,
} from './types'

export async function getMonthlyReport(month: string, signal?: AbortSignal): Promise<MonthlyReport> {
  const response = await apiClient.get<MonthlyReport>('/finance/reports/monthly', { params: { month }, signal })
  return response.data
}

export async function listTransactions(
  month: string,
  { limit = 100, offset = 0 }: { limit?: number; offset?: number } = {},
  signal?: AbortSignal,
): Promise<TransactionPage> {
  const response = await apiClient.get<TransactionPage>('/transactions', {
    params: { month, limit, offset },
    signal,
  })
  return response.data
}

export async function createTransaction(data: TransactionCreate): Promise<Transaction> {
  const response = await apiClient.post<Transaction>('/transactions', data)
  return response.data
}

export async function deleteTransaction(id: string): Promise<void> {
  await apiClient.delete(`/transactions/${id}`)
}

export async function listCategories(kind?: CategoryKind, signal?: AbortSignal): Promise<Category[]> {
  const response = await apiClient.get<Category[]>('/finance/categories', { params: { kind }, signal })
  return response.data
}

export async function createCategory(name: string, kind: CategoryKind): Promise<Category> {
  const response = await apiClient.post<Category>('/finance/categories', { name, kind })
  return response.data
}

export async function createBudget(data: BudgetCreate): Promise<Budget> {
  const response = await apiClient.post<Budget>('/budgets', data)
  return response.data
}

export async function updateBudget(id: string, amount: number): Promise<Budget> {
  const response = await apiClient.patch<Budget>(`/budgets/${id}`, { amount })
  return response.data
}

export async function deleteBudget(id: string): Promise<void> {
  await apiClient.delete(`/budgets/${id}`)
}
