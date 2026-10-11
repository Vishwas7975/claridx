import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from './client'

afterEach(() => {
  vi.unstubAllGlobals()
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
  })
})
