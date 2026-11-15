import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/services/api/errors'

import { getHealth } from '../api'
import { SystemStatusProvider } from '../SystemStatusProvider'
import type { HealthResponse } from '../types'
import { SystemStatusPanel } from './SystemStatusPanel'
import { SystemStatusIndicator } from './SystemStatusIndicator'

vi.mock('../api')

const healthy: HealthResponse = {
  status: 'ok',
  environment: 'development',
  version: '0.1.0',
  checks: { database: 'ok', llm: { status: 'ok', provider: 'ollama' } },
}

function renderStatus() {
  return render(
    <SystemStatusProvider>
      <SystemStatusPanel />
      <SystemStatusIndicator />
    </SystemStatusProvider>,
  )
}

describe('SystemStatusPanel and SystemStatusIndicator', () => {
  beforeEach(() => {
    vi.mocked(getHealth).mockReset()
  })

  it('show a loading state while the request is pending', () => {
    vi.mocked(getHealth).mockReturnValue(new Promise(() => {}))

    renderStatus()

    expect(screen.getByRole('status', { name: 'Đang kiểm tra kết nối tới Backend' })).toBeInTheDocument()
    expect(screen.getByText('Đang kiểm tra')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Kiểm tra lại' })).toBeDisabled()
  })

  it('share one request between every consumer', async () => {
    vi.mocked(getHealth).mockResolvedValue(healthy)

    renderStatus()

    await screen.findByText('Hoạt động bình thường')
    expect(getHealth).toHaveBeenCalledTimes(1)
  })

  it('show every check when the system is healthy', async () => {
    vi.mocked(getHealth).mockResolvedValue(healthy)

    renderStatus()

    expect(await screen.findByText('Hoạt động')).toBeInTheDocument()
    expect(screen.getByText('Kết nối tốt')).toBeInTheDocument()
    expect(screen.getByText('Sẵn sàng')).toBeInTheDocument()
    expect(screen.getByText('Phiên bản 0.1.0, môi trường development')).toBeInTheDocument()
    expect(screen.getByText('Hoạt động bình thường')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('report a degraded backend with a failing database', async () => {
    vi.mocked(getHealth).mockResolvedValue({
      ...healthy,
      status: 'degraded',
      checks: { ...healthy.checks, database: 'error' },
    })

    renderStatus()

    expect(await screen.findByText('Suy giảm')).toBeInTheDocument()
    expect(screen.getByText('Lỗi kết nối')).toBeInTheDocument()
    expect(screen.getByText('Hệ thống gặp sự cố')).toBeInTheDocument()
  })

  it('warn, without reporting a failure, when the LLM is not available', async () => {
    vi.mocked(getHealth).mockResolvedValue({
      ...healthy,
      checks: { database: 'ok', llm: { status: 'unavailable', provider: 'ollama' } },
    })

    renderStatus()

    expect(await screen.findByText('Chưa sẵn sàng')).toBeInTheDocument()
    expect(screen.getByText('AI (ollama)')).toBeInTheDocument()
    expect(screen.getByText('Hoạt động')).toBeInTheDocument()
    expect(screen.getByText('AI chưa sẵn sàng')).toBeInTheDocument()
  })

  it('show the error message and request id when the request fails', async () => {
    vi.mocked(getHealth).mockRejectedValue(
      new ApiError({ kind: 'server', message: 'Hệ thống gặp lỗi.', requestId: 'req-42' }),
    )

    renderStatus()

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Hệ thống gặp lỗi.')
    expect(alert).toHaveTextContent('req-42')
    expect(screen.getByText('Mất kết nối Backend')).toBeInTheDocument()
  })

  it.each(['Thử lại', 'Kiểm tra lại'])('request again when "%s" is clicked', async (buttonName) => {
    vi.mocked(getHealth)
      .mockRejectedValueOnce(new ApiError({ kind: 'network', message: 'Mất kết nối' }))
      .mockResolvedValueOnce(healthy)
    const user = userEvent.setup()

    renderStatus()
    await screen.findByRole('alert')
    await user.click(screen.getByRole('button', { name: buttonName }))

    expect(await screen.findByText('Hoạt động')).toBeInTheDocument()
    expect(getHealth).toHaveBeenCalledTimes(2)
  })
})
