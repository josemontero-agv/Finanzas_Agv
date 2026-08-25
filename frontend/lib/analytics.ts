import { flaskApi } from '@/lib/api'

const KNOWN_MODULES = new Set([
  'collections',
  'letters',
  'treasury',
  'dashboard',
  'diagnostics',
  'observability',
  'apps',
])

/** Última ruta registrada en esta sesión de navegación (dedupe page_view). */
let lastTrackedPath: string | null = null

export function moduleFromPath(path: string): string {
  const segment = path.split('/').filter(Boolean)[0]?.toLowerCase() || ''
  return KNOWN_MODULES.has(segment) ? segment : 'other'
}

/**
 * Emite un evento de telemetría sin bloquear la UI (fire-and-forget).
 * Fallos de red se ignoran a propósito.
 */
export function track(
  eventName: string,
  category: string,
  payload?: Record<string, unknown>,
  path?: string
): void {
  const resolvedPath =
    path || (typeof window !== 'undefined' ? window.location.pathname : undefined)

  void flaskApi
    .post('/api/v1/analytics/events', {
      event_category: category,
      event_name: eventName,
      payload: payload || {},
      path: resolvedPath,
    })
    .catch(() => {
      /* telemetría no debe afectar UX */
    })
}

/** page_view con dedupe de la misma path en la sesión de navegación actual. */
export function trackPageView(pathname: string): void {
  if (!pathname || pathname === '/login') return
  if (pathname === lastTrackedPath) return
  lastTrackedPath = pathname

  const module = moduleFromPath(pathname)
  track('page_view', 'nav', { path: pathname, module }, pathname)
}
