import { useState, useEffect, useRef } from 'react'
import { ThemeToggle } from './components/ThemeToggle'
import { ThemeProvider } from './context/ThemeContext'
import { AuthProvider, useAuth } from './features/auth/AuthContext'
import { LoginForm } from './features/auth/LoginForm'
import { RegisterForm } from './features/auth/RegisterForm'
import { RequestAccessPage } from './features/auth/RequestAccessPage'
import { ResearcherNotice } from './features/auth/ResearcherNotice'
import { PredictionPage as DiabetesPredictionPage } from './features/diabetes/PredictionPage'
import { PredictionPage as HeartPredictionPage } from './features/heart/PredictionPage'
import { LandingPage } from './features/landing/LandingPage'
import { PatientDashboard } from './features/patient/PatientDashboard'

export type Condition = 'heart' | 'diabetes'
export type View = 'landing' | 'login' | 'register' | 'request-access'

export interface AppProps {
  initialView?: View
}

export function AppContent({ initialView = 'landing' }: AppProps) {
  const { user, isAuthenticated, isLoading, logout } = useAuth()
  const [condition, setCondition] = useState<Condition>('heart')
  const [view, setView] = useState<View>(initialView)

  const wasAuthenticatedRef = useRef(isAuthenticated)
  useEffect(() => {
    if (wasAuthenticatedRef.current && !isAuthenticated) {
      setView('login')
    }
    wasAuthenticatedRef.current = isAuthenticated
  }, [isAuthenticated])

  const handleLogout = () => {
    setView('login')
    logout()
  }

  const isPatient = user?.role?.toLowerCase() === 'patient'
  const isResearcher = user?.role?.toLowerCase() === 'researcher'

  // If session has finished loading and user is an unauthenticated guest on landing view,
  // display the dedicated public landing page.
  if (!isLoading && !isAuthenticated && view === 'landing') {
    return (
      <div className="app-root">
        <LandingPage onNavigate={(nextView) => setView(nextView)} />
      </div>
    )
  }

  return (
    <div className="app-root">
      {/* ===== App Header ===== */}
      <header className="app-header">
        <div className="container header-inner">
          <div
            className="brand"
            onClick={() => {
              if (!isAuthenticated) setView('landing')
            }}
            style={{ cursor: !isAuthenticated ? 'pointer' : 'default' }}
            title={!isAuthenticated ? 'Return to ClariDx Home' : undefined}
          >
            <div className="brand-mark" aria-hidden="true">
              Cx
            </div>
            <div className="brand-text">
              <h1 className="brand-name">ClariDx</h1>
              <p className="brand-tagline">Clinical AI you can see through</p>
            </div>
          </div>

          <div className="header-actions-group">
            <ThemeToggle />

            {isAuthenticated && user ? (
              <nav className="user-nav" aria-label="User account">
                <div className="user-profile">
                  <span className="user-name">{user.full_name || user.email}</span>
                  <span
                    className={`role-badge role-${user.role.toLowerCase()}`}
                    aria-label={`Role: ${user.role}`}
                  >
                    {user.role.toUpperCase()}
                  </span>
                </div>
                <button
                  type="button"
                  className="sign-out-btn"
                  onClick={handleLogout}
                  aria-label="Sign out of ClariDx"
                >
                  Sign out
                </button>
              </nav>
            ) : (
              <button
                type="button"
                className="nav-link-btn"
                onClick={() => setView('landing')}
                style={{ fontSize: '0.875rem' }}
              >
                Back to Home
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ===== Disclaimer Banner ===== */}
      <div className="disclaimer-banner" role="note">
        Research prototype for decision support and education only. It is not a medical device and
        must not be used for diagnosis or treatment.
      </div>

      {/* ===== Main Content Area ===== */}
      <main className="app-main">
        <div className="container">
          {isLoading ? (
            <p role="status" className="session-loading">
              Loading session…
            </p>
          ) : !isAuthenticated ? (
            view === 'register' ? (
              <RegisterForm
                onBackToLogin={() => setView('login')}
                onBackToHome={() => setView('landing')}
              />
            ) : view === 'request-access' ? (
              <RequestAccessPage onBack={() => setView('login')} />
            ) : (
              <LoginForm
                onRequestAccess={() => setView('request-access')}
                onRegister={() => setView('register')}
                onBackToHome={() => setView('landing')}
              />
            )
          ) : isPatient ? (
            <PatientDashboard />
          ) : (
            <>
              {isResearcher && <ResearcherNotice />}

              <div className="workspace-header">
                <h1 className="workspace-title">
                  {isResearcher ? 'Model Inspection Workspace' : 'Clinical Decision Support'}
                </h1>
                <p className="workspace-subtitle">
                  {isResearcher
                    ? 'Inspect feature definitions and model parameters across conditions.'
                    : 'Analyse patient measurements and review explainable AI predictions.'}
                </p>
              </div>

              <nav className="condition-nav" aria-label="Condition selector">
                <button
                  type="button"
                  className={condition === 'heart' ? 'condition-btn active' : 'condition-btn'}
                  aria-pressed={condition === 'heart'}
                  onClick={() => setCondition('heart')}
                >
                  <span className="btn-icon" aria-hidden="true">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                    </svg>
                  </span>
                  Heart Disease
                </button>
                <button
                  type="button"
                  className={condition === 'diabetes' ? 'condition-btn active' : 'condition-btn'}
                  aria-pressed={condition === 'diabetes'}
                  onClick={() => setCondition('diabetes')}
                >
                  <span className="btn-icon" aria-hidden="true">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                    </svg>
                  </span>
                  Diabetes
                </button>
              </nav>

              {condition === 'heart' ? (
                <HeartPredictionPage key="heart" />
              ) : (
                <DiabetesPredictionPage key="diabetes" />
              )}
            </>
          )}
        </div>
      </main>

      {/* ===== App Footer ===== */}
      <footer className="app-footer">
        <div className="container footer-inner">
          <span className="footer-brand">ClariDx</span>
          <span className="footer-meta">
            Explainable AI for Clinical Decision Support · Research prototype only
          </span>
        </div>
      </footer>
    </div>
  )
}

export default function App({ initialView }: AppProps) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent initialView={initialView} />
      </AuthProvider>
    </ThemeProvider>
  )
}
