import createClient from 'openapi-fetch'
import type { paths } from './schema'

let activeToken: string | null = null
let unauthorizedHandler: (() => void) | null = null

export function setAuthToken(token: string | null): void {
  activeToken = token
}

export function getAuthToken(): string | null {
  return activeToken
}

export function onUnauthorized(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

export function shouldAttachToken(urlStr: string): boolean {
  if (!activeToken) return false
  try {
    const origin =
      typeof window !== 'undefined' && window.location ? window.location.origin : 'http://localhost'
    const url = new URL(urlStr, origin)
    return Boolean(origin && url.origin === origin)
  } catch {
    return false
  }
}

// An absolute base URL (the page's own origin) keeps request URLs valid outside the browser too.
// In development the Vite server proxies /api to the backend (see vite.config.ts).
// fetch is resolved on every call so tests can replace it.
export const api = createClient<paths>({
  baseUrl:
    typeof window !== 'undefined' && window.location ? window.location.origin : 'http://localhost',
  fetch: async (request) => {
    let req = request
    if (activeToken && shouldAttachToken(request.url) && !request.headers.has('Authorization')) {
      try {
        request.headers.set('Authorization', `Bearer ${activeToken}`)
      } catch {
        const headers = new Headers(request.headers)
        headers.set('Authorization', `Bearer ${activeToken}`)
        req = new Request(request, { headers })
      }
    }
    const response = await globalThis.fetch(req)
    if (
      response.status === 401 &&
      shouldAttachToken(req.url) &&
      !req.url.endsWith('/api/v1/auth/login')
    ) {
      unauthorizedHandler?.()
    }
    return response
  },
})
