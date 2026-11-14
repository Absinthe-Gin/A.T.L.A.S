import { Component, type ErrorInfo, type ReactNode } from 'react'

import { reportError } from '@/utils/reportError'

import { ErrorFallback } from './ErrorFallback'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

/**
 * Last line of defence for rendering errors outside the router.
 * Errors inside a route are handled by `RouteErrorPage`.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    reportError(error, { componentStack: info.componentStack })
  }

  private handleRetry = (): void => {
    this.setState({ hasError: false })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="mx-auto max-w-2xl p-6">
          <ErrorFallback onRetry={this.handleRetry} />
        </div>
      )
    }
    return this.props.children
  }
}
