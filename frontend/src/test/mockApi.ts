import { vi } from 'vitest'
import { setAuthToken } from '../api/client'
import type { UserProfile } from '../api/types'
import { diabetesFixture, diabetesModelsFixture, heartFixture } from './fixtures'

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export const defaultMockUser: UserProfile = {
  id: 1,
  email: 'doctor@claridx.test',
  full_name: 'Dr. Test Physician',
  role: 'doctor',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_login_at: '2026-01-01T00:00:00Z',
}

interface Handlers {
  features?: () => Response | Promise<Response>
  predictions?: () => Response | Promise<Response>
  diabetesFeatures?: () => Response | Promise<Response>
  diabetesModels?: () => Response | Promise<Response>
  diabetesPredictions?: () => Response | Promise<Response>
  register?: () => Response | Promise<Response>
  history?: () => Response | Promise<Response>
  login?: () => Response | Promise<Response>
  me?: () => Response | Promise<Response>
  authenticated?: boolean
  user?: UserProfile
}

export interface RecordedCall {
  path: string
  body: unknown
  authHeader?: string | null
}

/** Replaces fetch with an in-memory fake of the API and records prediction requests. */
export function mockApi(handlers: Handlers = {}): RecordedCall[] {
  const predictionCalls: RecordedCall[] = []

  if (handlers.authenticated !== false) {
    try {
      sessionStorage.setItem('claridx_token', 'mock-test-token')
      sessionStorage.setItem('claridx_user', JSON.stringify(handlers.user ?? defaultMockUser))
    } catch {
      // Ignore
    }
    setAuthToken('mock-test-token')
  } else {
    try {
      sessionStorage.removeItem('claridx_token')
      sessionStorage.removeItem('claridx_user')
    } catch {
      // Ignore
    }
    setAuthToken(null)
  }

  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const urlStr =
        typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
      const method = (
        (typeof input === 'object' && 'method' in input && input.method
          ? input.method
          : init?.method) || 'GET'
      ).toUpperCase()
      const path = new URL(urlStr, 'http://localhost').pathname

      async function getBody() {
        if (
          typeof input === 'object' &&
          input &&
          'json' in input &&
          typeof (input as Request).json === 'function'
        ) {
          try {
            return await (input as Request).clone().json()
          } catch {
            return undefined
          }
        }
        if (init?.body && typeof init.body === 'string') {
          try {
            return JSON.parse(init.body)
          } catch {
            return init.body
          }
        }
        return init?.body
      }

      function getHeader(name: string): string | null {
        if (
          typeof input === 'object' &&
          input &&
          'headers' in input &&
          (input as Request).headers
        ) {
          return (input as Request).headers.get(name)
        }
        if (init?.headers) {
          if (init.headers instanceof Headers) return init.headers.get(name)
          if (Array.isArray(init.headers)) {
            const pair = init.headers.find(([k]) => k.toLowerCase() === name.toLowerCase())
            return pair ? pair[1] : null
          }
          return (
            (init.headers as Record<string, string>)[name] ||
            (init.headers as Record<string, string>)[name.toLowerCase()] ||
            null
          )
        }
        return null
      }
      if (method === 'POST' && path === '/api/v1/auth/register') {
        if (handlers.register) return handlers.register()
        return json({ access_token: 'mock-test-token', token_type: 'bearer' }, 201)
      }
      if (method === 'GET' && path === '/api/v1/history') {
        if (handlers.history) return handlers.history()
        return json({ items: [], total: 0, limit: 20, offset: 0 })
      }
      if (method === 'GET' && path.startsWith('/api/v1/history/') && path.endsWith('/pdf')) {
        return new Response(new Uint8Array([37, 80, 68, 70, 45, 49, 46, 52]), {
          status: 200,
          headers: {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="claridx_report.pdf"',
          },
        })
      }
      if (method === 'POST' && path === '/api/v1/auth/login') {
        if (handlers.login) return handlers.login()
        return json({ access_token: 'mock-test-token', token_type: 'bearer' })
      }
      if (method === 'GET' && path === '/api/v1/auth/me') {
        if (handlers.me) return handlers.me()
        if (handlers.authenticated === false) {
          return json({ detail: 'Not authenticated' }, 401)
        }
        return json(handlers.user ?? defaultMockUser)
      }
      if (method === 'GET' && path === '/api/v1/heart/features') {
        return handlers.features ? handlers.features() : json(heartFixture.features)
      }
      if (method === 'POST' && path === '/api/v1/heart/predictions') {
        predictionCalls.push({
          path,
          body: await getBody(),
          authHeader: getHeader('Authorization'),
        })
        if (handlers.predictions === undefined) throw new Error('unexpected prediction request')
        return handlers.predictions()
      }
      if (method === 'GET' && path === '/api/v1/diabetes/features') {
        return handlers.diabetesFeatures
          ? handlers.diabetesFeatures()
          : json(diabetesFixture.features)
      }
      if (method === 'GET' && path === '/api/v1/diabetes/models') {
        return handlers.diabetesModels ? handlers.diabetesModels() : json(diabetesModelsFixture)
      }
      if (method === 'POST' && path === '/api/v1/diabetes/predictions') {
        predictionCalls.push({
          path,
          body: await getBody(),
          authHeader: getHeader('Authorization'),
        })
        if (handlers.diabetesPredictions === undefined) {
          throw new Error('unexpected diabetes prediction request')
        }
        return handlers.diabetesPredictions()
      }
      return json({ detail: `unexpected request: ${method} ${path}` }, 404)
    }),
  )
  return predictionCalls
}
