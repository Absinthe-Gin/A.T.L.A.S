import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ErrorBoundary } from './ErrorBoundary'

let shouldFail = false

function Unstable() {
  if (shouldFail) {
    throw new Error('render failure')
  }
  return <p>Nội dung bình thường</p>
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    shouldFail = false
    // React and reportError both log the caught error; keep test output clean.
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('renders its children when nothing fails', () => {
    render(
      <ErrorBoundary>
        <Unstable />
      </ErrorBoundary>,
    )

    expect(screen.getByText('Nội dung bình thường')).toBeInTheDocument()
  })

  it('shows a fallback and reports the error when a child fails', () => {
    shouldFail = true

    render(
      <ErrorBoundary>
        <Unstable />
      </ErrorBoundary>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('Đã xảy ra lỗi')
    expect(console.error).toHaveBeenCalledWith(
      '[app-error]',
      expect.objectContaining({ error: expect.any(Error) }),
    )
  })

  it('renders the children again after a successful retry', async () => {
    shouldFail = true
    const user = userEvent.setup()
    render(
      <ErrorBoundary>
        <Unstable />
      </ErrorBoundary>,
    )

    shouldFail = false
    await user.click(screen.getByRole('button', { name: 'Thử lại' }))

    expect(screen.getByText('Nội dung bình thường')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
