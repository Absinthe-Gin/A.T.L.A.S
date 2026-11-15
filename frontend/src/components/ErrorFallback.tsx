import { InlineAlert } from '@/components/ui/InlineAlert'

import { Button } from './ui/Button'

interface ErrorFallbackProps {
  title?: string
  onRetry?: () => void
}

/** Friendly message shown when part of the UI fails to render. */
export function ErrorFallback({ title = 'Đã xảy ra lỗi', onRetry }: ErrorFallbackProps) {
  return (
    <InlineAlert
      title={title}
      action={
        onRetry && (
          <Button variant="secondary" size="sm" onClick={onRetry}>
            Thử lại
          </Button>
        )
      }
    >
      Phần này của ứng dụng không hiển thị được. Bạn có thể thử lại hoặc tải lại trang.
    </InlineAlert>
  )
}
