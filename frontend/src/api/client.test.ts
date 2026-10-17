import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, getAuthToken, onUnauthorized, setAuthToken, shouldAttachToken } from './client'

afterEach(() => {
  vi.unstubAllGlobals()
  setAuthToken(null)
  onUnauthorized(null)
})

describe('api client', () => {
  it('sends typed requests to the page origin through the current global fetch', async () => {
    const seen: Request[] = []
    vi.stubGlobal(
      'fetch',
      vi.fn(async (request: Request) => {
        seen.push(request)
        return new Response('[]', { status: 200, headers: { 'Content-Type': 'application/json' } })
      }),
    )

    const { data } = await api.GET('/api/v1/heart/features')

    expect(data).toEqual([])
    expect(seen).toHaveLength(1)
    expect(new URL(seen[0].url).pathname).toBe('/api/v1/heart/features')
    expect(seen[0].headers.get('Authorization')).toBeNull()
  })

  it('attaches Authorization: Bearer <token> to requests targeting local origin when token is set', async () => {
    setAuthToken('test-bearer-token-123')
    expect(getAuthToken()).toBe('test-bearer-token-123')

    const seen: Request[] = []
    vi.stubGlobal(
      'fetch',
      vi.fn(async (request: Request) => {
        seen.push(request)
        return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } })
      }),
    )

    await api.POST('/api/v1/heart/predictions', {
      body: { model_name: 'random_forest', patient: { age: 50 } },
    })

    expect(seen).toHaveLength(1)
    expect(seen[0].headers.get('Authorization')).toBe('Bearer test-bearer-token-123')
  })

  it('does not attach bearer token to external URLs', () => {
    setAuthToken('secret-token')
    const externalUrl = 'https://unrelated-external-domain.org/api/data'
    expect(shouldAttachToken(externalUrl)).toBe(false)
  })

  it('triggers onUnauthorized callback when authenticated endpoint returns 401', async () => {
    setAuthToken('expired-token')
    const unauthorizedSpy = vi.fn()
    onUnauthorized(unauthorizedSpy)

    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        return new Response(JSON.stringify({ detail: 'Token expired' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      }),
    )

    await api.POST('/api/v1/heart/predictions', {
      body: { model_name: 'random_forest', patient: { age: 50 } },
    })

    expect(unauthorizedSpy).toHaveBeenCalledTimes(1)
  })

  it('does not trigger onUnauthorized for login failures returning 401', async () => {
    setAuthToken(null)
    const unauthorizedSpy = vi.fn()
    onUnauthorized(unauthorizedSpy)

    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        return new Response(JSON.stringify({ detail: 'Incorrect email or password' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        })
      }),
    )

    await api.POST('/api/v1/auth/login', {
      body: { email: 'bad@test.org', password: 'wrong' },
    })

    expect(unauthorizedSpy).not.toHaveBeenCalled()
  })
})
