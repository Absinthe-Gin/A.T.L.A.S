import { type FormEvent, useId, useState } from 'react'

import { IconClose, IconMapPin } from '@/components/icons'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { errorClasses, fieldClasses, labelClasses } from '@/components/ui/fieldClasses'
import { IconButton } from '@/components/ui/IconButton'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'

import { daysBetween, formatTime, formatWeekday } from '../format'
import type { MutationResult } from '../hooks/useTravelPlans'
import { stopNumbers } from '../itinerary'
import type { ItemCreate, ItineraryItem, Place, PlanDetail } from '../types'
import { PlaceSearch } from '@/features/places'

function groupByDay(items: ItineraryItem[]): [string | null, ItineraryItem[]][] {
  const groups = new Map<string | null, ItineraryItem[]>()
  for (const item of items) {
    const group = groups.get(item.day) ?? []
    group.push(item)
    groups.set(item.day, group)
  }
  return [...groups.entries()]
}

interface ItineraryProps {
  plan: PlanDetail
  saving: boolean
  onAdd: (data: ItemCreate) => Promise<MutationResult<unknown>>
  onDelete: (itemId: string) => void
}

export function Itinerary({ plan, saving, onAdd, onDelete }: ItineraryProps) {
  const numbers = stopNumbers(plan.items)
  return (
    <Card aria-labelledby="itinerary-heading" className="p-5">
      <h2 id="itinerary-heading" className="text-lg font-extrabold text-fg">
        Lịch trình
      </h2>

      {plan.items.length === 0 ? (
        <p className="mt-2 text-sm text-fg-muted">Chưa có hoạt động nào. Thêm điểm tham quan, quán ăn hay giờ di chuyển.</p>
      ) : (
        <div className="mt-3 space-y-5">
          {groupByDay(plan.items).map(([day, items]) => (
            <section key={day ?? 'unscheduled'} aria-label={day ? formatWeekday(day) : 'Chưa xếp ngày'}>
              <h3 className="text-sm font-bold text-note-yellow-ink">{day ? formatWeekday(day) : 'Chưa xếp ngày'}</h3>
              <ol className="mt-1 divide-y divide-border">
                {items.map((item) => (
                  <li key={item.id} className="flex animate-settle items-start gap-3 py-2.5">
                    <span className="w-12 shrink-0 pt-0.5 text-sm font-semibold text-fg-muted">
                      {item.start_time ? formatTime(item.start_time) : ''}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-fg">{item.title}</p>
                      {item.place && (
                        <p className="mt-0.5 flex items-center gap-1.5 text-xs text-fg-subtle">
                          <span className="flex size-4 items-center justify-center rounded-full bg-note-yellow text-[0.625rem] font-extrabold text-note-yellow-ink">
                            {numbers.get(item.id)}
                          </span>
                          {item.place.name}
                        </p>
                      )}
                      {item.note && <p className="mt-0.5 text-sm text-fg-muted">{item.note}</p>}
                    </div>
                    <IconButton
                      label={`Xóa hoạt động ${item.title}`}
                      icon={<IconClose size={16} />}
                      disabled={saving}
                      onClick={() => onDelete(item.id)}
                    />
                  </li>
                ))}
              </ol>
            </section>
          ))}
        </div>
      )}

      <ItemForm plan={plan} saving={saving} onAdd={onAdd} />
    </Card>
  )
}

function ItemForm({ plan, saving, onAdd }: Omit<ItineraryProps, 'onDelete'>) {
  const id = useId()
  const days = daysBetween(plan.start_date, plan.end_date)
  const [title, setTitle] = useState('')
  const [day, setDay] = useState(days[0] ?? '')
  const [time, setTime] = useState('')
  const [place, setPlace] = useState<Place | null>(null)
  // Remounts the place field after saving so it starts empty.
  const [formKey, setFormKey] = useState(0)
  const [touched, setTouched] = useState(false)
  const [serverError, setServerError] = useState<ApiError | null>(null)
  const titleError = title.trim() ? null : 'Nhập tên hoạt động.'

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    if (titleError) return
    setServerError(null)
    const result = await onAdd({
      title: title.trim(),
      day: day || null,
      start_time: time || null,
      place,
      note: null,
    })
    if (result.ok) {
      setTitle('')
      setTime('')
      setPlace(null)
      setTouched(false)
      setFormKey((key) => key + 1)
    } else {
      setServerError(result.error)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-labelledby={`${id}-title`}
      className="mt-5 space-y-3 rounded-control border border-dashed border-border-strong p-4"
    >
      <h3 id={`${id}-title`} className="flex items-center gap-2 text-sm font-bold text-fg">
        <IconMapPin size={16} className="text-primary" />
        Thêm hoạt động
      </h3>
      <div>
        <label htmlFor={`${id}-name`} className={labelClasses}>
          Hoạt động
        </label>
        <input
          id={`${id}-name`}
          maxLength={200}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Ví dụ: Dạo hồ Xuân Hương"
          aria-invalid={touched && titleError !== null}
          className={fieldClasses(touched && titleError !== null)}
        />
        {touched && titleError && <p className={errorClasses}>{titleError}</p>}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor={`${id}-day`} className={labelClasses}>
            Ngày
          </label>
          {days.length > 0 ? (
            <select id={`${id}-day`} value={day} onChange={(event) => setDay(event.target.value)} className={fieldClasses()}>
              <option value="">Chưa xếp ngày</option>
              {days.map((option) => (
                <option key={option} value={option}>
                  {formatWeekday(option)}
                </option>
              ))}
            </select>
          ) : (
            <input
              id={`${id}-day`}
              type="date"
              value={day}
              onChange={(event) => setDay(event.target.value)}
              className={fieldClasses()}
            />
          )}
        </div>
        <div>
          <label htmlFor={`${id}-time`} className={labelClasses}>
            Giờ
          </label>
          <input
            id={`${id}-time`}
            type="time"
            value={time}
            onChange={(event) => setTime(event.target.value)}
            className={fieldClasses()}
          />
        </div>
      </div>
      <PlaceSearch key={formKey} label="Địa điểm (không bắt buộc)" onSelect={setPlace} value={place} />
      {serverError && (
        <InlineAlert title="Chưa thêm được hoạt động" requestId={serverError.requestId}>
          {serverError.message}
        </InlineAlert>
      )}
      <Button type="submit" variant="secondary" loading={saving} className="w-full">
        Thêm vào lịch trình
      </Button>
    </form>
  )
}
