import { IconRefresh } from '@/components/icons'
import { Badge, type BadgeTone } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { IconButton } from '@/components/ui/IconButton'
import { InlineAlert } from '@/components/ui/InlineAlert'

import { useSystemStatus } from '../context'
import type { HealthResponse } from '../types'

interface Check {
  name: string
  detail: string
  tone: BadgeTone
  status: string
}

function checksOf(health: HealthResponse): Check[] {
  const backendOk = health.status === 'ok'
  const databaseOk = health.checks.database === 'ok'
  const llmOk = health.checks.llm.status === 'ok'
  return [
    {
      name: 'Backend',
      detail: `Phiên bản ${health.version}, môi trường ${health.environment}`,
      tone: backendOk ? 'success' : 'danger',
      status: backendOk ? 'Hoạt động' : 'Suy giảm',
    },
    {
      name: 'Database',
      detail: 'SQLite',
      tone: databaseOk ? 'success' : 'danger',
      status: databaseOk ? 'Kết nối tốt' : 'Lỗi kết nối',
    },
    {
      name: `AI (${health.checks.llm.provider})`,
      detail: llmOk ? 'Sẵn sàng trả lời' : 'Chat chưa dùng được',
      // The rest of the app works without the LLM, so this is a warning, not an error.
      tone: llmOk ? 'success' : 'warning',
      status: llmOk ? 'Sẵn sàng' : 'Chưa sẵn sàng',
    },
  ]
}

function LoadingRows() {
  return (
    <div role="status" aria-label="Đang kiểm tra kết nối tới Backend" className="divide-y divide-border">
      {[0, 1, 2].map((row) => (
        <div key={row} className="space-y-1.5 py-3" aria-hidden="true">
          <div className="h-3 w-20 animate-pulse rounded bg-surface-2" />
          <div className="h-2.5 w-36 animate-pulse rounded bg-surface-2" />
        </div>
      ))}
    </div>
  )
}

/** Each dependency the app relies on, with its current state. */
export function SystemStatusPanel() {
  const health = useSystemStatus()

  return (
    <section aria-labelledby="system-status-heading">
      <div className="flex items-center justify-between border-b border-border pb-2">
        <h2 id="system-status-heading" className="text-lg font-extrabold text-fg">
          Trạng thái hệ thống
        </h2>
        <IconButton
          label="Kiểm tra lại"
          // Turns while checking: the click is acknowledged until the answer arrives.
          icon={<IconRefresh size={18} className={health.status === 'loading' ? 'animate-spin' : undefined} />}
          onClick={health.reload}
          disabled={health.status === 'loading'}
          // Keep the header as tall as its text so it lines up with neighbouring headings.
          className="-my-2 -mr-2"
        />
      </div>

      {health.status === 'loading' && <LoadingRows />}
      {health.status === 'error' && (
        <InlineAlert
          className="mt-3"
          title="Không lấy được trạng thái hệ thống"
          requestId={health.error.requestId}
          action={
            <Button variant="secondary" size="sm" onClick={health.reload}>
              Thử lại
            </Button>
          }
        >
          {health.error.message}
        </InlineAlert>
      )}
      {health.status === 'success' && (
        <ul className="animate-settle divide-y divide-border">
          {checksOf(health.data).map((check) => (
            <li key={check.name} className="flex items-start justify-between gap-3 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-fg">{check.name}</p>
                <p className="text-xs text-fg-subtle">{check.detail}</p>
              </div>
              <Badge tone={check.tone} dot>
                {check.status}
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
