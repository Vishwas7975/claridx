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
    vi.fn(async (request: Request) => {
      const path = new URL(request.url).pathname
      if (request.method === 'POST' && path === '/api/v1/auth/login') {
        if (handlers.login) return handlers.login()
        return json({ access_token: 'mock-test-token', token_type: 'bearer' })
      }
      if (request.method === 'GET' && path === '/api/v1/auth/me') {
        if (handlers.me) return handlers.me()
        if (handlers.authenticated === false) {
          return json({ detail: 'Not authenticated' }, 401)
        }
        return json(handlers.user ?? defaultMockUser)
      }
      if (request.method === 'GET' && path === '/api/v1/heart/features') {
        return handlers.features ? handlers.features() : json(heartFixture.features)
      }
      if (request.method === 'POST' && path === '/api/v1/heart/predictions') {
        predictionCalls.push({
          path,
          body: await request.json(),
          authHeader: request.headers.get('Authorization'),
        })
        if (handlers.predictions === undefined) throw new Error('unexpected prediction request')
        return handlers.predictions()
      }
      if (request.method === 'GET' && path === '/api/v1/diabetes/features') {
        return handlers.diabetesFeatures
          ? handlers.diabetesFeatures()
          : json(diabetesFixture.features)
      }
      if (request.method === 'GET' && path === '/api/v1/diabetes/models') {
        return handlers.diabetesModels ? handlers.diabetesModels() : json(diabetesModelsFixture)
      }
      if (request.method === 'POST' && path === '/api/v1/diabetes/predictions') {
        predictionCalls.push({
          path,
          body: await request.json(),
          authHeader: request.headers.get('Authorization'),
        })
        if (handlers.diabetesPredictions === undefined) {
          throw new Error('unexpected diabetes prediction request')
        }
        return handlers.diabetesPredictions()
      }
      return json({ detail: `unexpected request: ${request.method} ${path}` }, 404)
    }),
  )
  return predictionCalls
}
