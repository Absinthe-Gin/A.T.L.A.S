import { Link } from 'react-router'

/** A globe of meridians with one fixed position: where the user is now. */
function AtlasGlyph() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true" className="shrink-0">
      <circle cx="16" cy="16" r="13" stroke="var(--fg)" strokeWidth="1.5" />
      <ellipse cx="16" cy="16" rx="6" ry="13" stroke="var(--fg)" strokeWidth="1.25" />
      <path d="M3.5 12h25M3.5 20h25" stroke="var(--fg)" strokeWidth="1.25" />
      <circle cx="21.5" cy="11" r="3.25" fill="var(--primary)" stroke="var(--surface)" strokeWidth="1.5" />
    </svg>
  )
}

interface BrandMarkProps {
  /** Only the globe, for the folded sidebar. */
  compact?: boolean
}

export function BrandMark({ compact = false }: BrandMarkProps) {
  return (
    <Link
      to="/"
      className={compact ? 'flex justify-center rounded-control' : 'flex items-center gap-2.5 rounded-control'}
      aria-label="Atlas, về trang tổng quan"
    >
      <AtlasGlyph />
      {!compact && (
        <span className="leading-tight">
          <span className="block text-lg font-semibold tracking-tight text-fg">Atlas</span>
          <span className="block text-xs text-fg-subtle">Trợ lý cá nhân</span>
        </span>
      )}
    </Link>
  )
}
