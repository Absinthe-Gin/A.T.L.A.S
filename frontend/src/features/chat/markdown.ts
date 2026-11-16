/**
 * A small Markdown subset for assistant replies: paragraphs, headings, bullet and
 * numbered lists, fenced code, **bold**, *italic*, `code` and http(s) links.
 *
 * The result is a tree rendered as React elements, never as HTML strings, so text
 * from the model cannot inject markup or scripts.
 */

export type Inline =
  | { type: 'text'; text: string }
  | { type: 'strong'; children: Inline[] }
  | { type: 'em'; children: Inline[] }
  | { type: 'code'; text: string }
  | { type: 'link'; href: string; children: Inline[] }

export type Block =
  | { type: 'paragraph'; children: Inline[] }
  | { type: 'heading'; level: 1 | 2 | 3; children: Inline[] }
  | { type: 'list'; ordered: boolean; start: number; items: Inline[][] }
  | { type: 'code'; language: string | null; text: string }

const FENCE = /^```\s*([\w+-]*)\s*$/
const HEADING = /^(#{1,6})\s+(.*)$/
const BULLET = /^\s*[-*+]\s+(.*)$/
const NUMBERED = /^\s*(\d+)[.)]\s+(.*)$/
const SAFE_URL = /^https?:\/\/[^\s]+$/i

/** Inline markup, read left to right. Unmatched markers stay as plain text. */
export function parseInline(text: string): Inline[] {
  const nodes: Inline[] = []
  let buffer = ''
  const flush = () => {
    if (buffer) nodes.push({ type: 'text', text: buffer })
    buffer = ''
  }

  let i = 0
  while (i < text.length) {
    const rest = text.slice(i)

    if (rest.startsWith('`')) {
      const end = text.indexOf('`', i + 1)
      if (end > i + 1) {
        flush()
        nodes.push({ type: 'code', text: text.slice(i + 1, end) })
        i = end + 1
        continue
      }
    }

    if (rest.startsWith('**') || rest.startsWith('__')) {
      const marker = rest.slice(0, 2)
      const end = text.indexOf(marker, i + 2)
      if (end > i + 2) {
        flush()
        nodes.push({ type: 'strong', children: parseInline(text.slice(i + 2, end)) })
        i = end + 2
        continue
      }
    }

    if ((rest.startsWith('*') || rest.startsWith('_')) && !/\s/.test(text[i + 1] ?? ' ')) {
      const marker = rest[0]
      const end = text.indexOf(marker, i + 1)
      // `_` inside a word (snake_case) is not emphasis.
      const wordBefore = marker === '_' && /\w/.test(text[i - 1] ?? '')
      if (end > i + 1 && !wordBefore && !/\s/.test(text[end - 1])) {
        flush()
        nodes.push({ type: 'em', children: parseInline(text.slice(i + 1, end)) })
        i = end + 1
        continue
      }
    }

    if (rest.startsWith('[')) {
      const match = /^\[([^\]]+)\]\(([^)\s]+)\)/.exec(rest)
      if (match && SAFE_URL.test(match[2])) {
        flush()
        nodes.push({ type: 'link', href: match[2], children: parseInline(match[1]) })
        i += match[0].length
        continue
      }
    }

    buffer += text[i]
    i += 1
  }
  flush()
  return nodes
}

/** Split a reply into blocks. Lines are kept as written; nothing is dropped. */
export function parseMarkdown(source: string): Block[] {
  const lines = source.replace(/\r\n?/g, '\n').split('\n')
  const blocks: Block[] = []
  let paragraph: string[] = []

  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: 'paragraph', children: parseInline(paragraph.join('\n')) })
    paragraph = []
  }

  let i = 0
  while (i < lines.length) {
    const line = lines[i]

    const fence = FENCE.exec(line)
    if (fence) {
      flushParagraph()
      const body: string[] = []
      i += 1
      while (i < lines.length && !FENCE.test(lines[i])) {
        body.push(lines[i])
        i += 1
      }
      blocks.push({ type: 'code', language: fence[1] || null, text: body.join('\n') })
      i += 1 // closing fence, if any
      continue
    }

    if (!line.trim()) {
      flushParagraph()
      i += 1
      continue
    }

    const heading = HEADING.exec(line)
    if (heading) {
      flushParagraph()
      const level = Math.min(heading[1].length, 3) as 1 | 2 | 3
      blocks.push({ type: 'heading', level, children: parseInline(heading[2].trim()) })
      i += 1
      continue
    }

    const bullet = BULLET.exec(line)
    const numbered = NUMBERED.exec(line)
    if (bullet || numbered) {
      flushParagraph()
      const ordered = !bullet
      const pattern = ordered ? NUMBERED : BULLET
      const start = numbered ? Number(numbered[1]) : 1
      const items: Inline[][] = []
      while (i < lines.length && pattern.test(lines[i])) {
        const match = pattern.exec(lines[i])!
        items.push(parseInline((ordered ? match[2] : match[1]).trim()))
        i += 1
      }
      blocks.push({ type: 'list', ordered, start, items })
      continue
    }

    paragraph.push(line)
    i += 1
  }
  flushParagraph()
  return blocks
}
