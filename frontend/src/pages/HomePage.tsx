import { SystemStatusCard } from '@/features/system-status/components/SystemStatusCard'

export function HomePage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Xin chào</h1>
        <p className="mt-1 text-slate-600">
          Nền tảng AI Personal Assistant đã sẵn sàng. Các chức năng sẽ được bổ sung theo từng giai
          đoạn.
        </p>
      </header>
      <SystemStatusCard />
    </div>
  )
}
