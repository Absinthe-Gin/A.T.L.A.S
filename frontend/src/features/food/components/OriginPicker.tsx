import { useState } from 'react'

import { Button } from '@/components/ui/Button'
import { hintClasses } from '@/components/ui/fieldClasses'
import { PlaceSearch, type Place } from '@/features/places'

interface OriginPickerProps {
  origin: Place | null
  onChange: (origin: Place) => void
}

/**
 * Where the user is. Either a place typed by name, or the browser's location when
 * permission is granted. The location is only kept on screen, never stored.
 */
export function OriginPicker({ origin, onChange }: OriginPickerProps) {
  const [locating, setLocating] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Trình duyệt này không hỗ trợ định vị. Hãy nhập tên khu vực.')
      return
    }
    setLocating(true)
    setLocationError(null)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocating(false)
        onChange({
          name: 'Vị trí hiện tại',
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        })
      },
      () => {
        setLocating(false)
        setLocationError('Chưa lấy được vị trí. Hãy cho phép định vị hoặc nhập tên khu vực.')
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 5 * 60_000 },
    )
  }

  return (
    <div className="space-y-2">
      <PlaceSearch label="Bạn đang ở đâu?" onSelect={onChange} value={origin} placeholder="Ví dụ: Huế, Hà Nội" />
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="secondary" size="sm" onClick={useMyLocation} loading={locating}>
          Dùng vị trí của tôi
        </Button>
        {origin && <span className={hintClasses}>Đang chọn: {origin.name}</span>}
      </div>
      {locationError && <p className="text-xs font-medium text-danger">{locationError}</p>}
    </div>
  )
}
