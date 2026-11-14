interface ErrorFallbackProps {
  title?: string
  onRetry?: () => void
}

/** Friendly message shown when part of the UI fails to render. */
export function ErrorFallback({ title = 'Đã xảy ra lỗi', onRetry }: ErrorFallbackProps) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-6">
      <h2 className="text-lg font-semibold text-red-800">{title}</h2>
      <p className="mt-2 text-sm text-red-700">
        Phần này của ứng dụng không hiển thị được. Bạn có thể thử lại hoặc tải lại trang.
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-md bg-red-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-600"
        >
          Thử lại
        </button>
      )}
    </div>
  )
}
