import { useState, type FormEvent } from 'react'
import { ApiError } from '../../api/errors'
import { useAuth } from './AuthContext'

export function LoginForm() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (submitting) return

    setErrorMessage(null)
    setSubmitting(true)

    try {
      await login({ email, password })
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setErrorMessage('Invalid email or password.')
        } else if (err.status === 403) {
          setErrorMessage('Your account is not authorized or is inactive.')
        } else {
          setErrorMessage('Unable to sign in. Please verify your connection and try again.')
        }
      } else {
        setErrorMessage('Unable to sign in. Please verify your connection and try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const canSubmit = email.trim().length > 0 && password.length > 0 && !submitting

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Sign in to ClariDx</h2>
        <p className="login-subtitle">
          Authorized clinical and research personnel sign in to access diagnostic models.
        </p>

        {errorMessage && (
          <p role="alert" className="error-banner">
            {errorMessage}
          </p>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="login-email">Email address</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setErrorMessage(null)
              }}
              disabled={submitting}
              required
              autoComplete="username"
              placeholder="name@hospital.org"
            />
          </div>

          <div className="form-field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                setErrorMessage(null)
              }}
              disabled={submitting}
              required
              autoComplete="current-password"
              placeholder="••••••••"
            />
          </div>

          <div className="actions">
            <button type="submit" disabled={!canSubmit}>
              {submitting ? 'Signing in\u2026' : 'Sign in'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
