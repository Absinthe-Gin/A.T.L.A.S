/** `1480.2` → `1.480 km`; short distances keep one decimal, e.g. `3,4 km`. Pure. */
export function formatDistance(km: number): string {
  if (km < 10) return `${km.toLocaleString('vi-VN', { maximumFractionDigits: 1 })} km`
  return `${Math.round(km).toLocaleString('vi-VN')} km`
}
