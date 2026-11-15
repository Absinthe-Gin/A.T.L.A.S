/** A named point: a place chosen by the user, stored with a plan or used as an origin. */
export interface Place {
  name: string
  lat: number
  lon: number
}

/** A place search result from OpenStreetMap (`GeoPlace`). Optional fields may be missing in the source. */
export interface GeoPlace extends Place {
  display_name: string
  category: string | null
  type: string | null
  osm_type: string | null
  osm_id: number | null
}
