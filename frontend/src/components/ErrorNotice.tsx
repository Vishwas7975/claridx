import { describeError } from '../api/errors'

interface Props {
  title: string
  error: Error
  onRetry?: () => void
}

export function ErrorNotice({ title, error, onRetry }: Props) {
  return (
    <div className="notice error" role="alert">
      <strong>{title}</strong>
      <p>{describeError(error)}</p>
      {onRetry && (
        <div style={{ marginTop: '0.75rem' }}>
          <button type="button" className="secondary sm" onClick={() => onRetry()}>
            Try again
          </button>
        </div>
      )}
    </div>
  )
}
