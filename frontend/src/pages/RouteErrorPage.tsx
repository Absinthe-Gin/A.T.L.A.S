import { useEffect } from 'react'
import { useRouteError } from 'react-router'

import { ErrorFallback } from '@/components/ErrorFallback'
import { reportError } from '@/utils/reportError'

/** Shown in place of a page that failed, so the layout and navigation stay usable. */
export function RouteErrorPage() {
  const error = useRouteError()

  useEffect(() => {
    reportError(error, { source: 'route' })
  }, [error])

  return <ErrorFallback title="Trang này gặp lỗi" />
}
