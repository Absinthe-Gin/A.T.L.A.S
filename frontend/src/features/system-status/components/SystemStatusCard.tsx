import { useHealthStatus } from '../hooks/useHealthStatus'
import type { HealthResponse } from '../types'

const BADGE_BASE = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-sm font-medium'
const BADGE_OK = `${BADGE_BASE} bg-emerald-100 text-emerald-800`
const BADGE_PROBLEM = `${BADGE_BASE} bg-red-100 text-red-800`

function HealthDetails({ health }: { health: HealthResponse }) {
  const isHealthy = health.status === 'ok'
  const isDatabaseOk = health.checks.database === 'ok'

  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
      <dt className="text-slate-500">Backend</dt>
      <dd>
        <span className={isHealthy ? BADGE_OK : BADGE_PROBLEM}>
          {isHealthy ? 'Hoạt động' : 'Suy giảm'}
        </span>
      </dd>
      <dt className="text-slate-500">Database</dt>
      <dd>
        <span className={isDatabaseOk ? BADGE_OK : BADGE_PROBLEM}>
          {isDatabaseOk ? 'Kết nối tốt' : 'Lỗi kết nối'}
        </span>
      </dd>
      <dt className="text-slate-500">Môi trường</dt>
      <dd>{health.environment}</dd>
      <dt className="text-slate-500">Phiên bản</dt>
      <dd>{health.version}</dd>
    </dl>
  )
}

export function SystemStatusCard() {
  const health = useHealthStatus()

  return (
    <section
      aria-labelledby="system-status-heading"
      className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
    >
      <h2 id="system-status-heading" className="mb-4 text-lg font-semibold">
        Trạng thái hệ thống
      </h2>

      {health.status === 'loading' && (
        <p role="status" className="text-sm text-slate-500">
          Đang kiểm tra kết nối tới Backend…
        </p>
      )}

      {health.status === 'error' && (
        <div role="alert" className="space-y-3 text-sm">
          <p className="text-red-700">{health.error.message}</p>
          {health.error.requestId && (
            <p className="text-slate-500">Mã yêu cầu: {health.error.requestId}</p>
          )}
          <button
            type="button"
            onClick={health.reload}
            className="rounded-md bg-slate-900 px-3 py-1.5 font-medium text-white hover:bg-slate-700"
          >
            Thử lại
          </button>
        </div>
      )}

      {health.status === 'success' && <HealthDetails health={health.data} />}
    </section>
  )
}
