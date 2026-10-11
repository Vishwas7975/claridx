export interface FieldIssue {
  /** Name of the patient field the server complained about; null for general problems. */
  field: string | null
  message: string
}

export class ApiError extends Error {
  readonly status: number
  readonly issues: FieldIssue[]

  constructor(message: string, status: number, issues: FieldIssue[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.issues = issues
  }
}

function toIssue(raw: unknown): FieldIssue | null {
  if (typeof raw !== 'object' || raw === null) return null
  const { loc, msg } = raw as { loc?: unknown; msg?: unknown }
  if (typeof msg !== 'string') return null
  const path = Array.isArray(loc) ? loc.map(String) : []
  const field = path[0] === 'body' && path[1] === 'patient' && path.length === 3 ? path[2] : null
  return { field, message: msg.replace(/^Value error, /, '') }
}

/**
 * The API answers errors in two shapes: a list of validation issues (HTTP 422) and a plain
 * string (for example HTTP 503 when the models are not loaded). Responses without a usable
 * body, such as a proxy's 502 when the backend is down, are described by status class.
 */
export function toApiError(error: unknown, status: number): ApiError {
  const detail =
    typeof error === 'object' && error !== null ? (error as { detail?: unknown }).detail : undefined
  if (typeof detail === 'string') return new ApiError(detail, status)
  if (Array.isArray(detail)) {
    const issues = detail.map(toIssue).filter((issue): issue is FieldIssue => issue !== null)
    return new ApiError('The server rejected some of the values.', status, issues)
  }
  if (status === 502 || status === 503 || status === 504) {
    return new ApiError(
      'The server is not reachable right now. Check that the backend is running and try again.',
      status,
    )
  }
  if (status >= 500) {
    return new ApiError(
      `The server reported an internal error (HTTP ${status}). Try again in a moment.`,
      status,
    )
  }
  return new ApiError(`The request failed (HTTP ${status}).`, status)
}

/** A message safe to show to the user for any thrown error. */
export function describeError(error: Error): string {
  if (error instanceof ApiError) return error.message
  return 'Cannot reach the server. Check that the backend is running and try again.'
}
