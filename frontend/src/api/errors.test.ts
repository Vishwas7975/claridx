import { describe, expect, it } from 'vitest'
import { ApiError, describeError, toApiError } from './errors'

describe('toApiError', () => {
  it('uses a plain-string detail (HTTP 503 style) as the message', () => {
    const error = toApiError({ detail: 'Prediction models are not loaded.' }, 503)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.message).toBe('Prediction models are not loaded.')
    expect(error.status).toBe(503)
    expect(error.issues).toEqual([])
  })

  it('maps validation issues to patient fields and strips the "Value error" prefix', () => {
    const error = toApiError(
      {
        detail: [
          {
            loc: ['body', 'patient', 'chol'],
            msg: 'Input should be less than or equal to 700',
            type: 'less_than_equal',
          },
          {
            loc: ['body', 'patient'],
            msg: 'Value error, At least 7 of 13 measurements are required; 5 provided.',
            type: 'value_error',
          },
        ],
      },
      422,
    )
    expect(error.status).toBe(422)
    expect(error.issues).toEqual([
      { field: 'chol', message: 'Input should be less than or equal to 700' },
      { field: null, message: 'At least 7 of 13 measurements are required; 5 provided.' },
    ])
  })

  it('ignores malformed issues instead of failing', () => {
    const error = toApiError({ detail: [null, 'text', { loc: ['body'] }, { msg: 5 }] }, 422)
    expect(error.issues).toEqual([])
  })

  it('describes gateway statuses without a usable body as the server being unreachable', () => {
    for (const status of [502, 503, 504]) {
      expect(toApiError(undefined, status).message).toMatch(/not reachable right now/)
      expect(toApiError('Bad Gateway', status).message).toMatch(/not reachable right now/)
    }
  })

  it('reports other server errors as internal errors', () => {
    expect(toApiError(undefined, 500).message).toBe(
      'The server reported an internal error (HTTP 500). Try again in a moment.',
    )
  })

  it('keeps a generic message for other statuses', () => {
    expect(toApiError({ other: 1 }, 404).message).toBe('The request failed (HTTP 404).')
  })
})

describe('describeError', () => {
  it('shows API errors as they are and everything else as a connection problem', () => {
    expect(describeError(new ApiError('Prediction models are not loaded.', 503))).toBe(
      'Prediction models are not loaded.',
    )
    expect(describeError(new TypeError('Failed to fetch'))).toMatch(/cannot reach the server/i)
  })
})
