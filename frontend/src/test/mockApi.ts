import { vi } from 'vitest'
import { diabetesFixture, diabetesModelsFixture, heartFixture } from './fixtures'

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

interface Handlers {
  features?: () => Response | Promise<Response>
  predictions?: () => Response | Promise<Response>
  diabetesFeatures?: () => Response | Promise<Response>
  diabetesModels?: () => Response | Promise<Response>
  diabetesPredictions?: () => Response | Promise<Response>
}

export interface RecordedCall {
  path: string
  body: unknown
}

/** Replaces fetch with an in-memory fake of the API and records prediction requests. */
export function mockApi(handlers: Handlers = {}): RecordedCall[] {
  const predictionCalls: RecordedCall[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (request: Request) => {
      const path = new URL(request.url).pathname
      if (request.method === 'GET' && path === '/api/v1/heart/features') {
        return handlers.features ? handlers.features() : json(heartFixture.features)
      }
      if (request.method === 'POST' && path === '/api/v1/heart/predictions') {
        predictionCalls.push({ path, body: await request.json() })
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
        predictionCalls.push({ path, body: await request.json() })
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
