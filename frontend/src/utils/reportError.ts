/**
 * Single entry point for reporting unexpected errors.
 * Replace the body to forward errors to a monitoring service.
 */
export function reportError(error: unknown, context: Record<string, unknown> = {}): void {
  console.error('[app-error]', { error, ...context })
}
