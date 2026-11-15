import { Link } from 'react-router'

import { IconCalendar, IconMapPin, IconPlane } from '@/components/icons'
import { EmptyState } from '@/components/ui/EmptyState'

import { formatDateRange } from '../format'
import type { Plan } from '../types'

export function PlanList({ plans, total }: { plans: Plan[]; total: number }) {
  if (plans.length === 0) {
    return (
      <EmptyState
        icon={<IconPlane />}
        title="Chưa có chuyến đi nào"
        description="Tạo chuyến đi đầu tiên ở bên cạnh, hoặc nhờ Trợ lý AI lập kế hoạch cho bạn."
      />
    )
  }
  return (
    <div className="space-y-3">
      <ul className="grid gap-3 sm:grid-cols-2">
        {plans.map((plan) => {
          const dates = formatDateRange(plan.start_date, plan.end_date)
          return (
            <li key={plan.id} className="animate-settle">
              <Link
                to={`/travel/${plan.id}`}
                className="block h-full rounded-card border border-border bg-surface p-4 shadow-raise transition-[border-color,translate] duration-150 hover:-translate-y-0.5 hover:border-primary/40 focus-visible:outline-2 focus-visible:outline-ring"
              >
                <p className="text-[0.9375rem] font-bold text-fg">{plan.title}</p>
                <dl className="mt-2 space-y-1 text-sm text-fg-muted">
                  <div className="flex items-center gap-2">
                    <dt className="sr-only">Điểm đến</dt>
                    <IconMapPin size={15} className="shrink-0 text-note-yellow-ink" />
                    <dd className="truncate">{plan.destination?.name ?? 'Chưa chọn điểm đến'}</dd>
                  </div>
                  <div className="flex items-center gap-2">
                    <dt className="sr-only">Thời gian</dt>
                    <IconCalendar size={15} className="shrink-0 text-note-yellow-ink" />
                    <dd>{dates ?? 'Chưa chọn ngày'}</dd>
                  </div>
                </dl>
                <p className="mt-3 text-xs font-semibold text-fg-subtle">
                  {plan.item_count === 0 ? 'Chưa có lịch trình' : `${plan.item_count} hoạt động`}
                </p>
              </Link>
            </li>
          )
        })}
      </ul>
      {total > plans.length && (
        <p className="text-sm text-fg-subtle">
          Đang hiện {plans.length} trên {total} chuyến đi.
        </p>
      )}
    </div>
  )
}
