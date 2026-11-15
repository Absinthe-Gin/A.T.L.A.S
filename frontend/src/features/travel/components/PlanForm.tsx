import { type FormEvent, useId, useState } from 'react'

import { Button } from '@/components/ui/Button'
import { errorClasses, fieldClasses, labelClasses } from '@/components/ui/fieldClasses'
import { InlineAlert } from '@/components/ui/InlineAlert'
import type { ApiError } from '@/services/api/errors'

import type { MutationResult } from '../hooks/useTravelPlans'
import type { Place, PlanCreate, PlanDetail } from '../types'
import { PlaceSearch } from '@/features/places'

interface PlanFormProps {
  onSubmit: (data: PlanCreate) => Promise<MutationResult<PlanDetail>>
  onCreated: (plan: PlanDetail) => void
  saving: boolean
}

export function PlanForm({ onSubmit, onCreated, saving }: PlanFormProps) {
  const id = useId()
  const [title, setTitle] = useState('')
  const [destination, setDestination] = useState<Place | null>(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [touched, setTouched] = useState(false)
  const [serverError, setServerError] = useState<ApiError | null>(null)

  const titleError = title.trim() ? null : 'Đặt tên cho chuyến đi.'
  const dateError = startDate && endDate && endDate < startDate ? 'Ngày về phải sau hoặc trùng ngày đi.' : null

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    if (titleError || dateError) return
    setServerError(null)
    const result = await onSubmit({
      title: title.trim(),
      destination,
      start_date: startDate || null,
      end_date: endDate || null,
      note: null,
    })
    if (result.ok) onCreated(result.value)
    else setServerError(result.error)
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`} className="text-lg font-extrabold text-fg">
        Chuyến đi mới
      </h2>

      <div>
        <label htmlFor={`${id}-name`} className={labelClasses}>
          Tên chuyến đi
        </label>
        <input
          id={`${id}-name`}
          maxLength={120}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Ví dụ: Đà Lạt cuối năm"
          aria-invalid={touched && titleError !== null}
          aria-describedby={`${id}-name-error`}
          className={fieldClasses(touched && titleError !== null)}
        />
        <p id={`${id}-name-error`} className={errorClasses} aria-live="polite">
          {touched ? titleError : null}
        </p>
      </div>

      <PlaceSearch label="Điểm đến" onSelect={setDestination} value={destination} />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor={`${id}-start`} className={labelClasses}>
            Ngày đi
          </label>
          <input
            id={`${id}-start`}
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
            className={fieldClasses()}
          />
        </div>
        <div>
          <label htmlFor={`${id}-end`} className={labelClasses}>
            Ngày về
          </label>
          <input
            id={`${id}-end`}
            type="date"
            value={endDate}
            min={startDate || undefined}
            onChange={(event) => setEndDate(event.target.value)}
            aria-invalid={dateError !== null}
            className={fieldClasses(touched && dateError !== null)}
          />
        </div>
      </div>
      {touched && dateError && <p className={errorClasses}>{dateError}</p>}

      {serverError && (
        <InlineAlert title="Chưa tạo được chuyến đi" requestId={serverError.requestId}>
          {serverError.message}
        </InlineAlert>
      )}

      <Button type="submit" loading={saving} className="w-full">
        Tạo chuyến đi
      </Button>
    </form>
  )
}
