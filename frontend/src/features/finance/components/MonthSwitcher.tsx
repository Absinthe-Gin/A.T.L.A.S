import { IconArrowRight } from '@/components/icons'
import { IconButton } from '@/components/ui/IconButton'
import { formatMonth, shiftMonth } from '@/utils/money'

interface MonthSwitcherProps {
  month: string
  onChange: (month: string) => void
}

export function MonthSwitcher({ month, onChange }: MonthSwitcherProps) {
  return (
    <div className="flex items-center gap-1 rounded-control border border-border-strong bg-surface p-1 shadow-raise">
      <IconButton
        label="Tháng trước"
        icon={<IconArrowRight size={18} className="rotate-180" />}
        onClick={() => onChange(shiftMonth(month, -1))}
      />
      <p className="min-w-32 text-center text-[0.9375rem] font-bold text-fg" aria-live="polite">
        {formatMonth(month)}
      </p>
      <IconButton label="Tháng sau" icon={<IconArrowRight size={18} />} onClick={() => onChange(shiftMonth(month, 1))} />
    </div>
  )
}
