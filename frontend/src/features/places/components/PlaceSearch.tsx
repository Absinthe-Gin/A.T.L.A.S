import { type KeyboardEvent, useId, useState } from 'react'

import { IconMapPin } from '@/components/icons'
import { Spinner } from '@/components/ui/Spinner'
import { errorClasses, fieldClasses, hintClasses, labelClasses } from '@/components/ui/fieldClasses'
import { cn } from '@/utils/cn'

import { MIN_QUERY_LENGTH, usePlaceSearch } from '../hooks/usePlaceSearch'
import type { GeoPlace, Place } from '../types'

interface PlaceSearchProps {
  label: string
  onSelect: (place: Place) => void
  placeholder?: string
  /** The currently chosen place, shown as the field's text. */
  value?: Place | null
  hint?: string
}

/** A combobox that searches OpenStreetMap as the user types. */
export function PlaceSearch({ label, onSelect, placeholder = 'Ví dụ: Đà Lạt, Hồ Gươm', value, hint }: PlaceSearchProps) {
  const id = useId()
  const [query, setQuery] = useState(value?.name ?? '')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const search = usePlaceSearch(open ? query : '')
  const places = search.places
  const listId = `${id}-list`
  const expanded = open && query.trim().length >= MIN_QUERY_LENGTH

  const choose = (place: GeoPlace) => {
    onSelect({ name: place.name, lat: place.lat, lon: place.lon })
    setQuery(place.name)
    setOpen(false)
    setActive(-1)
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown' && places.length > 0) {
      event.preventDefault()
      setOpen(true)
      setActive((current) => (current + 1) % places.length)
    } else if (event.key === 'ArrowUp' && places.length > 0) {
      event.preventDefault()
      setActive((current) => (current <= 0 ? places.length - 1 : current - 1))
    } else if (event.key === 'Enter' && open && active >= 0 && places[active]) {
      event.preventDefault()
      choose(places[active])
    } else if (event.key === 'Escape') {
      setOpen(false)
      setActive(-1)
    }
  }

  const status =
    search.status === 'error'
      ? search.error.message
      : search.status === 'success' && places.length === 0 && expanded
        ? 'Không tìm thấy địa điểm nào. Thử tên khác hoặc thêm tỉnh, thành phố.'
        : null

  return (
    <div className="relative">
      <label htmlFor={`${id}-input`} className={labelClasses}>
        {label}
      </label>
      <div className="relative">
        <input
          id={`${id}-input`}
          role="combobox"
          aria-expanded={expanded && places.length > 0}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={active >= 0 ? `${id}-option-${active}` : undefined}
          aria-describedby={`${id}-status`}
          autoComplete="off"
          value={query}
          placeholder={placeholder}
          onChange={(event) => {
            setQuery(event.target.value)
            setOpen(true)
            setActive(-1)
          }}
          onFocus={() => setOpen(true)}
          // Delay so a click on an option lands before the list closes.
          onBlur={() => window.setTimeout(() => setOpen(false), 150)}
          onKeyDown={handleKeyDown}
          className={cn(fieldClasses(search.status === 'error'), 'pr-10')}
        />
        {search.status === 'loading' && (
          <span className="absolute top-1/2 right-3 -translate-y-1/2 text-fg-subtle">
            <Spinner size={16} />
            <span className="sr-only">Đang tìm địa điểm</span>
          </span>
        )}
      </div>

      {expanded && places.length > 0 && (
        <ul
          id={listId}
          role="listbox"
          aria-label={`Kết quả cho ${query.trim()}`}
          className="absolute z-[1000] mt-1 max-h-72 w-full animate-pop overflow-auto rounded-control border border-border bg-surface p-1 shadow-lift"
        >
          {places.map((place, index) => (
            <li
              key={`${place.osm_type ?? 'p'}-${place.osm_id ?? index}-${place.lat}-${place.lon}`}
              id={`${id}-option-${index}`}
              role="option"
              aria-selected={index === active}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => choose(place)}
              className={cn(
                'flex cursor-pointer gap-2.5 rounded-[0.5rem] px-2.5 py-2',
                index === active ? 'bg-primary-soft' : 'hover:bg-surface-2',
              )}
            >
              <IconMapPin size={16} className="mt-0.5 shrink-0 text-primary" />
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold text-fg">{place.name}</span>
                <span className="block truncate text-xs text-fg-subtle">{place.display_name}</span>
              </span>
            </li>
          ))}
        </ul>
      )}

      <p id={`${id}-status`} aria-live="polite" className={status && search.status === 'error' ? errorClasses : hintClasses}>
        {status ?? hint ?? 'Dữ liệu địa điểm: © OpenStreetMap contributors'}
      </p>
    </div>
  )
}
