import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { Navigation } from './Navigation'

function renderNav(collapsed: boolean) {
  return render(
    <MemoryRouter initialEntries={['/finance']}>
      <Navigation collapsed={collapsed} />
    </MemoryRouter>,
  )
}

describe('Navigation', () => {
  it('shows every label and the status of planned modules when expanded', () => {
    renderNav(false)

    const finance = screen.getByRole('link', { name: /Tài chính/ })
    expect(within(finance).getByText('Tài chính')).toBeVisible()
    expect(screen.getByText('Sắp có', { selector: 'span' })).toBeInTheDocument()
  })

  it('folds to centred icons that keep their names for screen readers and tooltips', () => {
    renderNav(true)

    const finance = screen.getByRole('link', { name: 'Tài chính' })
    expect(finance).toHaveClass('justify-center')
    expect(finance).toHaveAttribute('title', 'Tài chính')
    expect(within(finance).getByText('Tài chính')).toHaveClass('sr-only')
    expect(screen.queryByText('Sắp có')).not.toBeInTheDocument()
    expect(finance).toHaveAttribute('aria-current', 'page')
  })
})
