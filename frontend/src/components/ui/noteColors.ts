export type StickyNoteColor = 'yellow' | 'peach' | 'green' | 'pink' | 'blue' | 'paper'

/** Paper colour of each note; also used for small swatches in the module's colour. */
export const NOTE_PAPER: Record<StickyNoteColor, string> = {
  yellow: 'bg-note-yellow',
  peach: 'bg-note-peach',
  green: 'bg-note-green',
  pink: 'bg-note-pink',
  blue: 'bg-note-blue',
  paper: 'bg-surface',
}

/** Ink that reads on each note colour (and is the module's identity colour). */
export const NOTE_INK: Record<StickyNoteColor, string> = {
  yellow: 'text-note-yellow-ink',
  peach: 'text-note-peach-ink',
  green: 'text-note-green-ink',
  pink: 'text-note-pink-ink',
  blue: 'text-note-blue-ink',
  paper: 'text-primary',
}
