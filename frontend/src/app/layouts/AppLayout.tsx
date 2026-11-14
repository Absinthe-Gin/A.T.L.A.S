import { Link, Outlet } from 'react-router'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <nav aria-label="Điều hướng chính" className="mx-auto flex max-w-5xl items-center px-4 py-3">
          <Link to="/" className="text-lg font-semibold">
            AI Personal Assistant
          </Link>
        </nav>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
