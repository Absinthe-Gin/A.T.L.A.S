import 'leaflet/dist/leaflet.css'

import L from 'leaflet'
import { useEffect, useRef } from 'react'

import { env } from '@/config/env'
import { cn } from '@/utils/cn'

import { addTilesWithFallback } from './tiles'

import type { Place } from '@/features/travel/types'

export type MarkerKind = 'destination' | 'stop' | 'selected'

export interface MapMarker {
  id: string
  place: Place
  kind: MarkerKind
  /** Short text inside the pin, e.g. the stop number. */
  badge?: string
}

/** Centre of Vietnam, shown when there is nothing to point at. */
const DEFAULT_CENTER: L.LatLngTuple = [16.2, 106.5]
const DEFAULT_ZOOM = 5
const SINGLE_ZOOM = 13

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`)
}

function pinIcon(marker: MapMarker): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div class="map-pin map-pin--${marker.kind}"><span>${escapeHtml(marker.badge ?? '')}</span></div>`,
    iconSize: [32, 32],
    // The pin's tip is its bottom-left corner, rotated to point down.
    iconAnchor: [16, 32],
    tooltipAnchor: [0, -30],
  })
}

interface PinMapProps {
  markers: MapMarker[]
  /** Accessible description of what the map shows. */
  label: string
  className?: string
}

/**
 * An OpenStreetMap map with pins. Leaflet manages its own DOM, so the map is
 * created once and markers are replaced when they change.
 */
export function PinMap({ markers, label, className }: PinMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const layerRef = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const map = L.map(containerRef.current, { scrollWheelZoom: false }).setView(DEFAULT_CENTER, DEFAULT_ZOOM)
    addTilesWithFallback(map, {
      primary: { url: env.mapTileUrl, attribution: env.mapAttribution },
      fallback: { url: env.mapFallbackTileUrl, attribution: env.mapFallbackAttribution },
    })
    mapRef.current = map
    layerRef.current = L.layerGroup().addTo(map)
    return () => {
      map.remove()
      mapRef.current = null
      layerRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    const layer = layerRef.current
    if (!map || !layer) return
    layer.clearLayers()
    for (const marker of markers) {
      L.marker([marker.place.lat, marker.place.lon], { icon: pinIcon(marker), title: marker.place.name, keyboard: true })
        .bindTooltip(escapeHtml(marker.place.name))
        .addTo(layer)
    }
    if (markers.length === 1) {
      map.setView([markers[0].place.lat, markers[0].place.lon], SINGLE_ZOOM)
    } else if (markers.length > 1) {
      map.fitBounds(L.latLngBounds(markers.map((m) => [m.place.lat, m.place.lon] as L.LatLngTuple)), {
        padding: [36, 36],
        maxZoom: 14,
      })
    }
  }, [markers])

  return (
    <div className={cn('map-frame overflow-hidden rounded-card border border-border', className)}>
      <div ref={containerRef} role="region" aria-label={label} className="size-full min-h-72" />
    </div>
  )
}
