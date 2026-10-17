import { useState, type FormEvent } from 'react'
import { ApiError } from '../../api/errors'
import { useAuth } from './AuthContext'

interface Props {
  onRequestAccess: () => void
}

export function LoginForm({ onRequestAccess }: Props) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
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
    <div className="login-page">
      <div className="login-split" role="main">
        {/* Left — branding panel */}
        <div className="login-brand-panel" aria-hidden="true">
          <div>
            <h2>Explainable AI for Clinical Decision Support</h2>
            <p className="login-brand-tagline">
              ClariDx provides transparent model predictions with SHAP and LIME explanations,
              helping clinical teams understand what drives each result.
            </p>
          </div>
          <div className="login-brand-divider" />
          <div className="login-features">
            <div className="login-feature">
              <div className="login-feature-icon">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                </svg>
              </div>
              <span>Heart disease risk assessment with 13 clinical features</span>
            </div>
            <div className="login-feature">
              <div className="login-feature-icon">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                </svg>
              </div>
              <span>Diabetes risk scoring from 8 diagnostic measurements</span>
            </div>
            <div className="login-feature">
              <div className="login-feature-icon">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.3-4.3" />
                </svg>
              </div>
              <span>SHAP + LIME explanations with cross-explainer agreement</span>
            </div>
            <div className="login-feature">
              <div className="login-feature-icon">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M3 3v18h18" />
                  <path d="m19 9-5 5-4-4-3 3" />
                </svg>
              </div>
              <span>Missing-data sensitivity analysis with imputation transparency</span>
            </div>
          </div>
        </div>

        {/* Right — form panel */}
        <div className="login-form-panel">
          <h2 className="login-form-title">Sign in to ClariDx</h2>
          <p className="login-form-subtitle">Authorized clinical and research personnel only.</p>

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
              <div className="password-wrapper">
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
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
                <button
                  type="button"
                  className="password-toggle"
                  aria-label={showPassword ? 'Hide entry' : 'Show entry'}
                  tabIndex={0}
                  onClick={() => setShowPassword((v) => !v)}
                >
                  {showPassword ? (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
                      <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
                      <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
                      <line x1="2" y1="2" x2="22" y2="22" />
                    </svg>
                  ) : (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div className="login-actions">
              <button type="submit" className="login-submit-btn" disabled={!canSubmit}>
                {submitting ? 'Signing in…' : 'Sign in'}
              </button>
            </div>
          </form>

          <p className="login-footer-link" style={{ marginTop: '1.5rem' }}>
            Need access?{' '}
            <a
              href="#request-access"
              onClick={(e) => {
                e.preventDefault()
                onRequestAccess()
              }}
            >
              Learn how to request an account
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
