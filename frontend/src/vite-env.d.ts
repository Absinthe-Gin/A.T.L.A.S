interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_DEV_SERVER_PORT?: string
  readonly VITE_MAP_TILE_URL?: string
  readonly VITE_MAP_ATTRIBUTION?: string
  readonly VITE_MAP_FALLBACK_TILE_URL?: string
  readonly VITE_MAP_FALLBACK_ATTRIBUTION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
