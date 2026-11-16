import { describe, expect, it } from 'vitest'

import { parseInline, parseMarkdown } from './markdown'

describe('parseInline', () => {
  it('reads bold, italic, code and links', () => {
    expect(parseInline('Chi **45.000 ₫** cho *phở*, mã `VN 101`, xem [Open-Meteo](https://open-meteo.com)')).toEqual([
      { type: 'text', text: 'Chi ' },
      { type: 'strong', children: [{ type: 'text', text: '45.000 ₫' }] },
      { type: 'text', text: ' cho ' },
      { type: 'em', children: [{ type: 'text', text: 'phở' }] },
      { type: 'text', text: ', mã ' },
      { type: 'code', text: 'VN 101' },
      { type: 'text', text: ', xem ' },
      { type: 'link', href: 'https://open-meteo.com', children: [{ type: 'text', text: 'Open-Meteo' }] },
    ])
  })

  it('keeps unsafe links and unmatched markers as plain text', () => {
    expect(parseInline('[bấm](javascript:alert(1))')).toEqual([{ type: 'text', text: '[bấm](javascript:alert(1))' }])
    expect(parseInline('2 * 3 = 6 và **chưa đóng')).toEqual([{ type: 'text', text: '2 * 3 = 6 và **chưa đóng' }])
  })

  it('does not treat underscores inside words as emphasis', () => {
    expect(parseInline('finance_create_transaction')).toEqual([{ type: 'text', text: 'finance_create_transaction' }])
  })

  it('never turns markup into HTML', () => {
    expect(parseInline('<img src=x onerror=alert(1)>')).toEqual([
      { type: 'text', text: '<img src=x onerror=alert(1)>' },
    ])
  })
})

describe('parseMarkdown', () => {
  it('splits paragraphs, headings and lists', () => {
    const blocks = parseMarkdown('## Dự báo\nHôm nay trời đẹp.\n\n- Nhiệt độ: 15°C\n- Độ ẩm: 98%\n\n1. Mang áo\n2. Mang ô')

    expect(blocks.map((block) => block.type)).toEqual(['heading', 'paragraph', 'list', 'list'])
    expect(blocks[2]).toMatchObject({ type: 'list', ordered: false, items: [[{ text: 'Nhiệt độ: 15°C' }], [{ text: 'Độ ẩm: 98%' }]] })
    expect(blocks[3]).toMatchObject({ type: 'list', ordered: true, start: 1 })
  })

  it('keeps fenced code exactly as written', () => {
    expect(parseMarkdown('```json\n{"a": **1**}\n```')).toEqual([
      { type: 'code', language: 'json', text: '{"a": **1**}' },
    ])
  })

  it('keeps line breaks inside a paragraph', () => {
    expect(parseMarkdown('Dòng một\nDòng hai')).toEqual([
      { type: 'paragraph', children: [{ type: 'text', text: 'Dòng một\nDòng hai' }] },
    ])
  })

  it('returns nothing for an empty reply', () => {
    expect(parseMarkdown('  \n ')).toEqual([])
  })
})
