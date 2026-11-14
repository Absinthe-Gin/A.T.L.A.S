import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import { getHealth } from '../api'
import type { HealthResponse } from '../types'
import { SystemStatusCard } from './SystemStatusCard'

vi.mock('../api')

const healthy: HealthResponse = {
  status: 'ok',
  environment: 'development',
  version: '0.1.0',
  checks: { database: 'ok', llm: { status: 'ok', provider: 'ollama' } },
}

describe('SystemStatusCard', () => {
  beforeEach(() => {
    vi.mocked(getHealth).mockReset()
  })

  it('shows a loading message while the request is pending', () => {
    vi.mocked(getHealth).mockReturnValue(new Promise(() => {}))

    render(<SystemStatusCard />)

    expect(screen.getByRole('status')).toHaveTextContent('Đang kiểm tra kết nối')
  })

  it('shows backend details when the backend is healthy', async () => {
    vi.mocked(getHealth).mockResolvedValue(healthy)

    render(<SystemStatusCard />)

    expect(await screen.findByText('Hoạt động')).toBeInTheDocument()
    expect(screen.getByText('Kết nối tốt')).toBeInTheDocument()
    expect(screen.getByText('Sẵn sàng')).toBeInTheDocument()
    expect(screen.getByText('development')).toBeInTheDocument()
    expect(screen.getByText('0.1.0')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('shows a degraded backend with a failing database', async () => {
    vi.mocked(getHealth).mockResolvedValue({
      ...healthy,
      status: 'degraded',
      checks: { ...healthy.checks, database: 'error' },
    })

    render(<SystemStatusCard />)

    expect(await screen.findByText('Suy giảm')).toBeInTheDocument()
    expect(screen.getByText('Lỗi kết nối')).toBeInTheDocument()
  })

  it('shows a warning when the LLM is not available', async () => {
    vi.mocked(getHealth).mockResolvedValue({
      ...healthy,
      checks: { database: 'ok', llm: { status: 'unavailable', provider: 'ollama' } },
    })

    render(<SystemStatusCard />)

    expect(await screen.findByText('Chưa sẵn sàng')).toBeInTheDocument()
    expect(screen.getByText('AI (ollama)')).toBeInTheDocument()
    expect(screen.getByText('Hoạt động')).toBeInTheDocument()
  })

  it('shows the error message and request id when the request fails', async () => {
    vi.mocked(getHealth).mockRejectedValue(
      new ApiError({ kind: 'server', message: 'Hệ thống gặp lỗi.', requestId: 'req-42' }),
    )

    render(<SystemStatusCard />)

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Hệ thống gặp lỗi.')
    expect(alert).toHaveTextContent('req-42')
  })

  it('retries when the user clicks the retry button', async () => {
    vi.mocked(getHealth)
      .mockRejectedValueOnce(new ApiError({ kind: 'network', message: 'Mất kết nối' }))
      .mockResolvedValueOnce(healthy)
    const user = userEvent.setup()

    render(<SystemStatusCard />)
    await user.click(await screen.findByRole('button', { name: 'Thử lại' }))

    expect(await screen.findByText('Hoạt động')).toBeInTheDocument()
    expect(getHealth).toHaveBeenCalledTimes(2)
  })
})
