import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import {
  createBudget,
  createTransaction,
  deleteTransaction,
  getMonthlyReport,
  listCategories,
  listTransactions,
} from '../api'
import type { Category, MonthlyReport, Transaction } from '../types'
import { FinanceMonth } from './FinanceMonth'

vi.mock('../api')

const categories: Category[] = [
  { id: 'c-food', name: 'Ăn uống', kind: 'expense' },
  { id: 'c-bills', name: 'Hóa đơn', kind: 'expense' },
  { id: 'c-salary', name: 'Lương', kind: 'income' },
]

const lunch: Transaction = {
  id: 't1',
  kind: 'expense',
  amount: 45_000,
  currency: 'VND',
  category_id: 'c-food',
  category_name: 'Ăn uống',
  occurred_on: '2026-11-15',
  note: 'Phở',
  created_at: '2026-11-15T05:00:00Z',
}

function report(overrides: Partial<MonthlyReport> = {}): MonthlyReport {
  return {
    month: '2026-11',
    currency: 'VND',
    income_total: 15_000_000,
    expense_total: 45_000,
    adjustment_total: -10_000,
    net: 14_945_000,
    transaction_count: 1,
    expense_by_category: [{ category_id: 'c-food', category_name: 'Ăn uống', total: 45_000 }],
    budgets: [],
    ...overrides,
  }
}

/** Formatted money in the page uses a no-break space before ₫. */
const money = (text: string) =>
  new RegExp(text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(' ', '\\s'))

describe('FinanceMonth', () => {
  beforeEach(() => {
    vi.mocked(getMonthlyReport).mockReset().mockResolvedValue(report())
    vi.mocked(listTransactions).mockReset().mockResolvedValue({ items: [lunch], total: 1, limit: 100, offset: 0 })
    vi.mocked(listCategories).mockReset().mockResolvedValue(categories)
    vi.mocked(createTransaction).mockReset()
    vi.mocked(deleteTransaction).mockReset()
    vi.mocked(createBudget).mockReset()
  })

  it('shows a loading state, then the totals computed by the backend', async () => {
    render(<FinanceMonth month="2026-11" />)

    expect(screen.getByRole('status', { name: 'Đang tải số liệu tháng' })).toBeInTheDocument()
    expect(await screen.findByText(money('15.000.000 ₫'))).toBeInTheDocument()
    expect(screen.getByText(money('+14.945.000 ₫'))).toBeInTheDocument()
    expect(screen.getByText(money('-10.000 ₫'))).toBeInTheDocument()
    expect(getMonthlyReport).toHaveBeenCalledWith('2026-11', expect.any(AbortSignal))
  })

  it('lists the month transactions grouped by day', async () => {
    render(<FinanceMonth month="2026-11" />)

    const day = await screen.findByRole('region', { name: /15\/11/ })
    expect(within(day).getByText('Phở')).toBeInTheDocument()
    expect(within(day).getByText(money('−45.000 ₫'))).toBeInTheDocument()
  })

  it('invites a first entry when the month is empty', async () => {
    vi.mocked(listTransactions).mockResolvedValue({ items: [], total: 0, limit: 100, offset: 0 })

    render(<FinanceMonth month="2026-11" />)

    expect(await screen.findByText(/chưa có giao dịch/)).toBeInTheDocument()
  })

  it('saves a transaction typed the Vietnamese way and refreshes the month', async () => {
    vi.mocked(createTransaction).mockResolvedValue(lunch)
    const user = userEvent.setup()
    render(<FinanceMonth month="2026-11" />)
    await screen.findByText('Phở')

    await user.type(screen.getByLabelText('Số tiền'), '1,5tr')
    expect(screen.getByText(money('= 1.500.000 ₫'))).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Danh mục'), 'c-bills')
    await user.type(screen.getByLabelText('Ghi chú'), 'Tiền điện')
    await user.click(screen.getByRole('button', { name: 'Lưu giao dịch' }))

    await waitFor(() => expect(getMonthlyReport).toHaveBeenCalledTimes(2))
    expect(createTransaction).toHaveBeenCalledWith(
      expect.objectContaining({ kind: 'expense', amount: 1_500_000, category_id: 'c-bills', note: 'Tiền điện' }),
    )
    expect(screen.getByLabelText('Số tiền')).toHaveValue('')
  })

  it('blocks an invalid amount before calling the backend', async () => {
    const user = userEvent.setup()
    render(<FinanceMonth month="2026-11" />)
    await screen.findByText('Phở')

    await user.type(screen.getByLabelText('Số tiền'), 'nhiều tiền')
    await user.click(screen.getByRole('button', { name: 'Lưu giao dịch' }))

    expect(screen.getByLabelText('Số tiền')).toHaveAttribute('aria-invalid', 'true')
    expect(createTransaction).not.toHaveBeenCalled()
  })

  it('lets an adjustment be negative and hides the category', async () => {
    vi.mocked(createTransaction).mockResolvedValue(lunch)
    const user = userEvent.setup()
    render(<FinanceMonth month="2026-11" />)
    await screen.findByText('Phở')

    await user.click(screen.getByLabelText('Điều chỉnh'))
    expect(screen.queryByLabelText('Danh mục')).not.toBeInTheDocument()
    await user.type(screen.getByLabelText('Số tiền'), '-20k')
    await user.click(screen.getByRole('button', { name: 'Lưu giao dịch' }))

    await waitFor(() =>
      expect(createTransaction).toHaveBeenCalledWith(
        expect.objectContaining({ kind: 'adjustment', amount: -20_000, category_id: null }),
      ),
    )
  })

  it('shows the backend error next to the form and keeps the input', async () => {
    vi.mocked(createTransaction).mockRejectedValue(
      new ApiError({ kind: 'business', message: 'Danh mục không cùng loại với giao dịch.', requestId: 'r-7' }),
    )
    const user = userEvent.setup()
    render(<FinanceMonth month="2026-11" />)
    await screen.findByText('Phở')

    await user.type(screen.getByLabelText('Số tiền'), '50k')
    await user.click(screen.getByRole('button', { name: 'Lưu giao dịch' }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Danh mục không cùng loại với giao dịch.')
    expect(alert).toHaveTextContent('r-7')
    expect(screen.getByLabelText('Số tiền')).toHaveValue('50k')
  })

  it('asks before deleting a transaction', async () => {
    vi.mocked(deleteTransaction).mockResolvedValue()
    const user = userEvent.setup()
    render(<FinanceMonth month="2026-11" />)

    await user.click(await screen.findByRole('button', { name: 'Xóa giao dịch Phở' }))
    expect(deleteTransaction).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Xóa' }))

    expect(deleteTransaction).toHaveBeenCalledWith('t1')
  })

  it('shows budget usage and over-spending in words', async () => {
    vi.mocked(getMonthlyReport).mockResolvedValue(
      report({
        budgets: [
          {
            id: 'b1',
            month: '2026-11',
            category_id: 'c-food',
            category_name: 'Ăn uống',
            amount: 40_000,
            spent: 45_000,
            remaining: -5_000,
            used_percent: 112,
            over_budget: true,
          },
        ],
      }),
    )
    render(<FinanceMonth month="2026-11" />)

    expect(await screen.findByText(money('Vượt 5.000 ₫'))).toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'Đã dùng ngân sách Ăn uống' })).toHaveAttribute(
      'aria-valuetext',
      '112%',
    )
  })

  it('creates a budget for the month', async () => {
    vi.mocked(createBudget).mockResolvedValue({
      id: 'b2',
      month: '2026-11',
      category_id: null,
      category_name: null,
      amount: 3_000_000,
      spent: 0,
      remaining: 3_000_000,
      used_percent: 0,
      over_budget: false,
    })
    const user = userEvent.setup()
    render(<FinanceMonth month="2026-11" />)
    await screen.findByText('Phở')

    await user.type(screen.getByLabelText('Hạn mức'), '3tr')
    await user.click(screen.getByRole('button', { name: 'Đặt ngân sách' }))

    await waitFor(() =>
      expect(createBudget).toHaveBeenCalledWith({ month: '2026-11', category_id: null, amount: 3_000_000 }),
    )
  })

  it('offers a retry when the month cannot be loaded', async () => {
    vi.mocked(getMonthlyReport)
      .mockRejectedValueOnce(new ApiError({ kind: 'network', message: 'Không kết nối được tới máy chủ.' }))
      .mockResolvedValueOnce(report())
    const user = userEvent.setup()
    render(<FinanceMonth month="2026-11" />)

    await user.click(await screen.findByRole('button', { name: 'Thử lại' }))

    expect(await screen.findByText('Phở')).toBeInTheDocument()
  })
})
