import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import type { PendingAction } from '../types'
import { PendingActionCard } from './PendingActionCard'

const proposal: PendingAction = {
  id: 'a1',
  tool_name: 'finance_create_transaction',
  summary: 'Ghi chi 50.000 ₫, danh mục Ăn uống, ngày 15/11/2026.',
  status: 'pending',
  error_message: null,
}

describe('PendingActionCard', () => {
  it('shows the proposal with confirm and cancel buttons', () => {
    render(<PendingActionCard action={proposal} onResolve={vi.fn()} />)

    expect(screen.getByText(proposal.summary)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Xác nhận' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Hủy' })).toBeEnabled()
  })

  it.each([
    ['Xác nhận', 'confirm'],
    ['Hủy', 'cancel'],
  ] as const)('sends the decision when "%s" is pressed', async (button, decision) => {
    const onResolve = vi.fn().mockResolvedValue(null)
    const user = userEvent.setup()
    render(<PendingActionCard action={proposal} onResolve={onResolve} />)

    await user.click(screen.getByRole('button', { name: button }))

    expect(onResolve).toHaveBeenCalledWith('a1', decision)
  })

  it.each([
    ['confirmed', 'Đã lưu.'],
    ['cancelled', 'Đã hủy, không có gì thay đổi.'],
  ] as const)('shows the outcome once %s', (status, text) => {
    render(<PendingActionCard action={{ ...proposal, status }} onResolve={vi.fn()} />)

    expect(screen.getByRole('status')).toHaveTextContent(text)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('explains a refusal by the backend', () => {
    render(
      <PendingActionCard
        action={{ ...proposal, status: 'failed', error_message: 'Không tìm thấy danh mục.' }}
        onResolve={vi.fn()}
      />,
    )

    expect(screen.getByRole('status')).toHaveTextContent('Không thực hiện được. Không tìm thấy danh mục.')
  })

  it('keeps the buttons and shows the error when the request fails', async () => {
    const onResolve = vi.fn().mockResolvedValue(new ApiError({ kind: 'network', message: 'Mất kết nối', requestId: 'r1' }))
    const user = userEvent.setup()
    render(<PendingActionCard action={proposal} onResolve={onResolve} />)

    await user.click(screen.getByRole('button', { name: 'Xác nhận' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Mất kết nối')
    expect(screen.getByRole('button', { name: 'Xác nhận' })).toBeEnabled()
  })
})
