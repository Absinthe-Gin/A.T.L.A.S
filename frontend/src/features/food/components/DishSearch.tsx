import { type FormEvent, useId, useState } from 'react'

import { Button } from '@/components/ui/Button'
import { errorClasses, fieldClasses, labelClasses } from '@/components/ui/fieldClasses'
import { formatDistance } from '@/utils/distance'

import { RADIUS_OPTIONS_M, type RadiusM } from '../types'

export const MIN_DISH_LENGTH = 2

interface DishSearchProps {
  dish: string
  onDishChange: (dish: string) => void
  radiusM: RadiusM
  onRadiusChange: (radius: RadiusM) => void
  onSubmit: () => void
  searching: boolean
}

export function DishSearch({
  dish,
  onDishChange,
  radiusM,
  onRadiusChange,
  onSubmit,
  searching,
}: DishSearchProps) {
  const id = useId()
  const [touched, setTouched] = useState(false)
  const trimmed = dish.trim()
  const error = trimmed.length >= MIN_DISH_LENGTH ? null : `Nhập tên món, ít nhất ${MIN_DISH_LENGTH} ký tự.`

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    setTouched(true)
    if (error) return
    onSubmit()
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-labelledby={`${id}-title`} className="space-y-4">
      <h2 id={`${id}-title`} className="text-lg font-extrabold text-fg">
        Tìm quán theo món
      </h2>
      <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_9rem] sm:items-start">
        <div>
          <label htmlFor={`${id}-dish`} className={labelClasses}>
            Món ăn
          </label>
          <input
            id={`${id}-dish`}
            value={dish}
            maxLength={80}
            onChange={(event) => onDishChange(event.target.value)}
            placeholder="Ví dụ: bún bò, phở, cơm tấm"
            aria-invalid={touched && error !== null}
            aria-describedby={`${id}-dish-error`}
            className={fieldClasses(touched && error !== null)}
          />
          <p id={`${id}-dish-error`} className={errorClasses} aria-live="polite">
            {touched ? error : null}
          </p>
        </div>
        <div>
          <label htmlFor={`${id}-radius`} className={labelClasses}>
            Bán kính
          </label>
          <select
            id={`${id}-radius`}
            value={radiusM}
            onChange={(event) => onRadiusChange(Number(event.target.value) as RadiusM)}
            className={fieldClasses()}
          >
            {RADIUS_OPTIONS_M.map((metres) => (
              <option key={metres} value={metres}>
                Trong {formatDistance(metres / 1000)}
              </option>
            ))}
          </select>
        </div>
      </div>
      <Button type="submit" loading={searching} className="w-full sm:w-auto">
        Tìm quán
      </Button>
    </form>
  )
}
