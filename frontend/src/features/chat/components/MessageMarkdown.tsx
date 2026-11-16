import { type ReactNode, useMemo } from 'react'

import { type Block, type Inline, parseMarkdown } from '../markdown'

function renderInline(nodes: Inline[], keyPrefix: string): ReactNode[] {
  return nodes.map((node, index) => {
    const key = `${keyPrefix}-${index}`
    switch (node.type) {
      case 'text':
        return node.text
      case 'strong':
        return (
          <strong key={key} className="font-bold text-fg">
            {renderInline(node.children, key)}
          </strong>
        )
      case 'em':
        return <em key={key}>{renderInline(node.children, key)}</em>
      case 'code':
        return (
          <code key={key} className="rounded-[0.3rem] bg-surface-2 px-1.5 py-0.5 font-mono text-[0.85em] text-fg">
            {node.text}
          </code>
        )
      case 'link':
        return (
          <a
            key={key}
            href={node.href}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-primary underline decoration-primary/40 underline-offset-2 hover:decoration-primary"
          >
            {renderInline(node.children, key)}
          </a>
        )
    }
  })
}

function renderBlock(block: Block, index: number): ReactNode {
  const key = `b${index}`
  switch (block.type) {
    case 'paragraph':
      return (
        <p key={key} className="whitespace-pre-wrap">
          {renderInline(block.children, key)}
        </p>
      )
    case 'heading': {
      const Tag = block.level === 1 ? 'h3' : block.level === 2 ? 'h4' : 'h5'
      return (
        <Tag key={key} className="pt-1 text-base font-extrabold text-fg">
          {renderInline(block.children, key)}
        </Tag>
      )
    }
    case 'list': {
      const items = block.items.map((item, itemIndex) => (
        // Items of one reply never reorder; their position is their identity.
        <li key={`${key}-${itemIndex}`} className="pl-1">
          {renderInline(item, `${key}-${itemIndex}`)}
        </li>
      ))
      return block.ordered ? (
        <ol key={key} start={block.start} className="list-decimal space-y-1 pl-6 marker:text-fg-subtle">
          {items}
        </ol>
      ) : (
        <ul key={key} className="list-disc space-y-1 pl-6 marker:text-fg-subtle">
          {items}
        </ul>
      )
    }
    case 'code':
      return (
        <pre
          key={key}
          className="overflow-x-auto rounded-control border border-border bg-surface-2 p-3 font-mono text-[0.8125rem] leading-relaxed text-fg"
        >
          <code>{block.text}</code>
        </pre>
      )
  }
}

/** An assistant reply with simple formatting. Rendered as elements, never as raw HTML. */
export function MessageMarkdown({ content }: { content: string }) {
  const blocks = useMemo(() => parseMarkdown(content), [content])
  return <div className="space-y-3 break-words text-[0.9375rem] leading-relaxed text-fg">{blocks.map(renderBlock)}</div>
}
