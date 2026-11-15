import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { MODULES } from '../catalog'
import { ModuleNotes } from './ModuleNotes'

const businessModules = MODULES.filter((module) => module.id !== 'dashboard')

function renderNotes() {
  return render(
    <MemoryRouter>
      <ModuleNotes />
    </MemoryRouter>,
  )
}

describe('ModuleNotes', () => {
  it('gives every module one note that links to it', () => {
    renderNotes()

    for (const module of businessModules) {
      expect(screen.getByRole('link', { name: module.label })).toHaveAttribute('href', module.path)
    }
    expect(screen.getAllByRole('listitem')).toHaveLength(businessModules.length)
  })

  it('names each module heading, so the notes can be scanned by heading', () => {
    renderNotes()

    expect(screen.getAllByRole('heading', { level: 3 }).map((heading) => heading.textContent)).toEqual(
      businessModules.map((module) => module.label),
    )
  })

  it('states the status of each module in words', () => {
    renderNotes()

    expect(screen.getAllByText('Đang hoạt động')).toHaveLength(
      businessModules.filter((module) => module.status === 'available').length,
    )
    expect(screen.getAllByText('Sắp có')).toHaveLength(
      businessModules.filter((module) => module.status === 'planned').length,
    )
  })
})
