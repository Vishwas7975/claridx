import createClient from 'openapi-fetch'
import type { paths } from './schema'

// An absolute base URL (the page's own origin) keeps request URLs valid outside the browser too.
// In development the Vite server proxies /api to the backend (see vite.config.ts).
// fetch is resolved on every call so tests can replace it.
export const api = createClient<paths>({
  baseUrl: window.location.origin,
  fetch: (request) => globalThis.fetch(request),
})
