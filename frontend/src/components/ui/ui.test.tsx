import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Badge } from './Badge'
import { Button } from './Button'
import { IconButton } from './IconButton'
import { InlineAlert } from './InlineAlert'

describe('Button', () => {
  it('is a non-submitting button by default', () => {
    render(<Button>Lưu</Button>)

    expect(screen.getByRole('button', { name: 'Lưu' })).toHaveAttribute('type', 'button')
  })

  it('is disabled and busy while loading', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(
      <Button loading onClick={onClick}>
        Lưu
      </Button>,
    )
    const button = screen.getByRole('button', { name: 'Lưu' })

    await user.click(button)

    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')
    expect(onClick).not.toHaveBeenCalled()
  })
})

describe('IconButton', () => {
  it('uses its label as the accessible name and tooltip', () => {
    render(<IconButton label="Đóng" icon={<svg />} />)

    const button = screen.getByRole('button', { name: 'Đóng' })
    expect(button).toHaveAttribute('title', 'Đóng')
  })
})

describe('InlineAlert', () => {
  it('interrupts for errors and is polite for warnings', () => {
    render(
      <>
        <InlineAlert title="Lỗi" requestId="req-1" />
        <InlineAlert tone="warning" title="Cảnh báo" />
      </>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('Lỗi')
    expect(screen.getByRole('alert')).toHaveTextContent('Mã yêu cầu: req-1')
    expect(screen.getByRole('status')).toHaveTextContent('Cảnh báo')
  })
})

describe('Badge', () => {
  it('always shows its text, so colour is never the only signal', () => {
    render(
      <Badge tone="danger" dot>
        Lỗi kết nối
      </Badge>,
    )

    expect(screen.getByText('Lỗi kết nối')).toBeVisible()
  })
})
